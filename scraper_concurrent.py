import sys
import json
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import DELAY_MIN, DELAY_MAX, OUTPUT_FILE
from utils import fetch_algolia_page, fetch_impel_details, fetch_vehicle_details, random_delay
from parsers import parse_algolia_hit, parse_impel_details, parse_vehicle_details, merge_vehicle_data
from database import init_db, is_vin_scraped, mark_vin_scraped

# Locks for thread-safe writing
db_lock = threading.Lock()
jsonl_lock = threading.Lock()
counter_lock = threading.Lock()

# Global counter for tracking progress
vehicles_saved_counter = 0
LONG_BREAK_INTERVAL = 10

# Rate limiter for API calls
last_api_call_time = 0
rate_limit_lock = threading.Lock()
MIN_TIME_BETWEEN_API_CALLS = 2  # seconds between ANY API call across threads

def rate_limited_api_call(func, *args, **kwargs):
    """Wrapper to rate-limit API calls across threads."""
    global last_api_call_time
    with rate_limit_lock:
        current_time = time.time()
        time_since_last = current_time - last_api_call_time
        if time_since_last < MIN_TIME_BETWEEN_API_CALLS:
            sleep_time = MIN_TIME_BETWEEN_API_CALLS - time_since_last
            time.sleep(sleep_time)
        last_api_call_time = time.time()
    return func(*args, **kwargs)

def process_vehicle_thread(hit):
    global vehicles_saved_counter
    vin = hit.get("vin")
    if not vin:
        return None
    
    # Check if already scraped (thread-safe read is okay as SQLite handles multiple readers)
    if is_vin_scraped(vin):
        print(f"Skipping already scraped VIN: {vin}")
        return None

    algolia_data = parse_algolia_hit(hit)
    impel_data = None
    ridemotive_data = None

    # Fetch Impel details for image fallback (with rate limiting)
    if hit.get("impel_enabled"):
        try:
            impel_json = rate_limited_api_call(fetch_impel_details, vin)
            impel_data = parse_impel_details(impel_json)
            # Small delay after API call
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Error fetching Impel details for {vin}: {e}")

    # Fetch RideMotive details for extended specs using vehicle_id (with rate limiting)
    vehicle_id = hit.get("id")
    if vehicle_id:
        try:
            ridemotive_json = rate_limited_api_call(fetch_vehicle_details, vehicle_id)
            ridemotive_data = parse_vehicle_details(ridemotive_json)
            # Small delay after API call
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Error fetching RideMotive details for {vehicle_id}: {e}")

    # Merge all data sources
    merged = merge_vehicle_data(algolia_data, impel_data, ridemotive_data)

    # Set image URL with priority: Algolia CDN > Impel thumb
    algolia_image = algolia_data.get("first_image_url")
    impel_thumb = merged.get("impel_thumb")
    if algolia_image:
        merged["first_image_url"] = algolia_image
    elif impel_thumb:
        merged["first_image_url"] = impel_thumb
    else:
        merged["first_image_url"] = None

    # Save to JSONL with lock
    with jsonl_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(merged, ensure_ascii=False) + "\n")
    
    # Mark in DB with lock
    with db_lock:
        mark_vin_scraped(
            merged.get("vin"),
            title=merged.get("car_name", ""),
            price=merged.get("price", ""),
            mileage=merged.get("mileage", ""),
            has_details=True
        )
    
    # Update counter
    with counter_lock:
        vehicles_saved_counter += 1
        current_count = vehicles_saved_counter
    
    print(f"Saved vehicle {vin} (total: {current_count})")
    
    return merged

def scrape_algolia_all_pages_seq(max_pages=None, max_hits=None, reverse=False):
    """Sequential fetch of Algolia pages. If reverse=True, processes from bottom-up."""
    all_hits = []
    page = 0
    while True:
        print(f"Fetching Algolia page {page}...")
        data = fetch_algolia_page(page)
        hits = data.get("hits", [])
        all_hits.extend(hits)
        nb_pages = data.get("nbPages", 0)
        nb_hits = data.get("nbHits", 0)
        print(f"Page {page}: {len(hits)} hits (total: {len(all_hits)}/{nb_hits})")
        page += 1
        if max_pages and page >= max_pages:
            break
        if page >= nb_pages:
            break
        if max_hits and len(all_hits) >= max_hits:
            all_hits = all_hits[:max_hits]
            break
        random_delay()
    
    # Reverse to process from bottom-up (last pages first)
    if reverse:
        print(f"Reversing hits order: will process from bottom-up (last {len(all_hits)} vehicles first)")
        all_hits.reverse()
    
    return all_hits

def run_concurrent(max_pages=1, max_vehicles=None, max_workers=3):
    init_db()
    
    # Fetch all hits sequentially (API pagination is sequential)
    # reverse=True: process from BOTTOM-UP (last pages first, for VPS concurrent)
    all_hits = scrape_algolia_all_pages_seq(max_pages=max_pages, max_hits=max_vehicles, reverse=True)
    print(f"Total hits fetched: {len(all_hits)}")
    
    if not all_hits:
        print("No hits to process.")
        return 0
    
    saved_count = 0
    # Process vehicles concurrently with delays between submissions (avoid burst API calls)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, hit in enumerate(all_hits):
            # Submit with small delay between tasks to avoid burst
            if i > 0:
                time.sleep(random.uniform(0.5, 1.5))
            future = executor.submit(process_vehicle_thread, hit)
            futures.append((future, hit))
        
        for future, hit in futures:
            try:
                result = future.result()
                if result:
                    saved_count += 1
            except Exception as e:
                vin = hit.get("vin", "unknown")
                print(f"Error processing VIN {vin}: {e}")
    
    print(f"Scraping complete. Total vehicles saved: {saved_count}")
    return saved_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Concurrent CarShop Scraper (for testing speed)")
    parser.add_argument("--pages", type=int, default=1, help="Number of Algolia pages to fetch")
    parser.add_argument("--max-vehicles", type=int, default=None, help="Max vehicles to process")
    parser.add_argument("--workers", type=int, default=3, help="Number of concurrent threads (default: 3)")
    args = parser.parse_args()
    
    print(f"Starting concurrent scraper (pages: {args.pages}, max vehicles: {args.max_vehicles}, workers: {args.workers})...")
    try:
        saved = run_concurrent(max_pages=args.pages, max_vehicles=args.max_vehicles, max_workers=args.workers)
        print(f"Successfully scraped {saved} vehicles")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)
