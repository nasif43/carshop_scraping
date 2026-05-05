import json
from utils import fetch_algolia_page, fetch_impel_details, fetch_vehicle_details, random_delay, long_break
from parsers import parse_algolia_hit, parse_impel_details, parse_vehicle_details, merge_vehicle_data
from database import is_vin_scraped, mark_vin_scraped, get_unprocessed_vins
from config import DELAY_MIN, DELAY_MAX, OUTPUT_FILE

# Take a longer break every N vehicles
LONG_BREAK_INTERVAL = 10

def scrape_algolia_all_pages(max_pages=None, max_hits=None):
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

    return all_hits

def process_vehicle(hit):
    vin = hit.get("vin")
    if not vin:
        return None

    if is_vin_scraped(vin):
        print(f"Skipping already scraped VIN: {vin}")
        return None

    algolia_data = parse_algolia_hit(hit)
    impel_data = None
    ridemotive_data = None

    # Fetch Impel details for image fallback
    if hit.get("impel_enabled"):
        try:
            print(f"Fetching Impel details for VIN: {vin}")
            impel_json = fetch_impel_details(vin)
            impel_data = parse_impel_details(impel_json)
            random_delay()
        except Exception as e:
            print(f"Error fetching Impel details for {vin}: {e}")

    # Fetch RideMotive details for extended specs using vehicle_id
    vehicle_id = hit.get("id")
    if vehicle_id:
        try:
            print(f"Fetching RideMotive details for vehicle_id: {vehicle_id}")
            ridemotive_json = fetch_vehicle_details(vehicle_id)
            ridemotive_data = parse_vehicle_details(ridemotive_json)
            random_delay()
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

    return merged

def save_to_jsonl(vehicles, output_file=OUTPUT_FILE):
    with open(output_file, "a", encoding="utf-8") as f:
        for vehicle in vehicles:
            f.write(json.dumps(vehicle, ensure_ascii=False) + "\n")
    print(f"Saved {len(vehicles)} vehicles to {output_file}")

def run_scraper(max_pages=1, max_vehicles=None):
    from database import init_db
    init_db()

    hits = scrape_algolia_all_pages(max_pages=max_pages, max_hits=max_vehicles)
    print(f"Total hits fetched: {len(hits)}")

    vehicles_saved = 0
    for i, hit in enumerate(hits):
        vehicle = process_vehicle(hit)
        if vehicle:
            # Save incrementally IMMEDIATELY
            save_to_jsonl([vehicle])
            
            # NOW mark in DB (AFTER saving to JSONL)
            mark_vin_scraped(
                vehicle.get("vin"),
                title=vehicle.get("car_name", ""),
                price=vehicle.get("price", ""),
                mileage=vehicle.get("mileage", ""),
                has_details=True
            )
            
            vehicles_saved += 1
            print(f"Progress: {vehicles_saved} vehicles saved to {OUTPUT_FILE}")
            
            # Take a longer break every N vehicles
            if vehicles_saved % LONG_BREAK_INTERVAL == 0 and vehicles_saved > 0:
                long_break()
            if max_vehicles and vehicles_saved >= max_vehicles:
                break

    print(f"Scraping complete. Total vehicles saved: {vehicles_saved}")
    return vehicles_saved
