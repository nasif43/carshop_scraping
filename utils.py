import time
import random
import json
import os
from curl_cffi import requests
from curl_cffi.requests.exceptions import ConnectionError, Timeout, HTTPError
from config import ALGOLIA_HEADERS, IMPEL_HEADERS, RIDEMOTIVE_HEADERS, DELAY_MIN, DELAY_MAX, ALGOLIA_ENDPOINT, ALGOLIA_APP_ID, ALGOLIA_API_KEY, ALGOLIA_INDEX, ALGOLIA_CACHE_DIR

# Impersonation targets for rotation (only supported versions)
# Common supported: chrome99, chrome100, chrome101, chrome104, chrome107, chrome110, chrome116, chrome119, chrome120, chrome123, chrome124
IMPERSIONATION_TARGETS = ["chrome110", "chrome120", "chrome123"]

def get_random_impersonation():
    return random.choice(IMPERSIONATION_TARGETS)

def fetch_with_retry(url, method="GET", headers=None, json_data=None, max_retries=3, impersonate_target=None):
    """Fetch with retry logic for rate limits and transient errors."""
    for attempt in range(max_retries):
        try:
            target = impersonate_target or get_random_impersonation()
            
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    json=json_data,
                    headers=headers,
                    impersonate=target,
                    timeout=15
                )
            else:
                response = requests.get(
                    url,
                    headers=headers,
                    impersonate=target,
                    timeout=15
                )
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"Rate limited (429). Waiting {retry_after}s before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_after)
                continue
            
            # Handle forbidden (403) - wait longer
            if response.status_code == 403:
                wait_time = (2 ** attempt) * 10  # Exponential backoff: 10s, 20s, 40s
                print(f"Forbidden (403). Waiting {wait_time}s before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response
            
        except (ConnectionError, Timeout) as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 5
                print(f"Connection error: {e}. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1 and "timeout" in str(e).lower():
                wait_time = (2 ** attempt) * 5
                print(f"Timeout error. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} retries")

def random_delay():
    """Random delay between requests with jitter."""
    delay = random.uniform(DELAY_MIN, DELAY_MAX)
    # Add small jitter
    jitter = random.uniform(-0.5, 0.5)
    final_delay = max(DELAY_MIN, delay + jitter)
    time.sleep(final_delay)

def long_break():
    """Take a longer break every N requests to simulate human behavior."""
    break_time = random.uniform(30, 60)
    print(f"Taking a longer break for {break_time:.1f}s to avoid detection...")
    time.sleep(break_time)

def fetch_algolia_page(page=0, user_token=None, use_cache=True, fresh_fetch=False):
    if user_token is None:
        from config import generate_user_token
        user_token = generate_user_token()

    # Setup cache
    os.makedirs(ALGOLIA_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(ALGOLIA_CACHE_DIR, f"page_{page}.json")

    # Try to load from cache if caching is enabled and not forcing fresh fetch
    if use_cache and not fresh_fetch and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            # Validate cache has required fields
            if "hits" in cached_data and "nbPages" in cached_data:
                print(f"Loading Algolia page {page} from cache")
                return cached_data, False
        except (json.JSONDecodeError, IOError):
            # Corrupted cache, delete and fetch fresh
            os.remove(cache_file)

    # Fetch from API
    print(f"Fetching Algolia page {page} from API")

    payload = {
        "query": "",
        "clickAnalytics": True,
        "userToken": user_token,
        "filters": "is_active:true AND dealer_ids:\"429\" AND dealership:\"CarShop Hatfield\"<score=3> OR dealership:\"CarShop Cranberry\"<score=1> OR dealership:\"CarShop Chester Springs\"<score=2> OR dealership:\"CarShop Glen Mills\"<score=2> OR dealership:\"CarShop Mount Holly\"<score=2> OR dealership:\"CarShop Robinson\"<score=1>",
        "optionalFilters": [],
        "page": page,
        "hitsPerPage": 36
    }

    headers = ALGOLIA_HEADERS.copy()
    headers["x-algolia-api-key"] = ALGOLIA_API_KEY
    headers["x-algolia-application-id"] = ALGOLIA_APP_ID

    response = fetch_with_retry(
        ALGOLIA_ENDPOINT,
        method="POST",
        headers=headers,
        json_data=payload
    )
    data = response.json()

    # Save to cache if caching is enabled
    if use_cache:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to cache Algolia page {page}: {e}")

    return data, True

def fetch_impel_details(vin):
    # Impel API requires lowercase VIN
    vin_lower = vin.lower() if vin else vin
    url = f"https://api.impel.io/spin/carsenserobinsontwp/{vin_lower}"
    response = fetch_with_retry(
        url,
        method="GET",
        headers=IMPEL_HEADERS
    )
    return response.json()

def fetch_vehicle_details(vehicle_id):
    url = f"https://api.app.ridemotive.com/vehicles/{vehicle_id}/vehicle_details"
    response = fetch_with_retry(
        url,
        method="GET",
        headers=RIDEMOTIVE_HEADERS
    )
    return response.json()

def extract_image_url(image_key, cdn_prefix=""):
    if not image_key:
        return None
    if image_key.startswith("http"):
        return image_key
    return f"{cdn_prefix.rstrip('/')}/{image_key}" if cdn_prefix else image_key

def format_car_name(hit):
    parts = [str(hit.get("make_year", "")), hit.get("make", ""), hit.get("model", "")]
    if hit.get("car_trim"):
        parts.append(hit.get("car_trim"))
    return " ".join(filter(None, parts)).strip()
