import argparse
import sys
from scraper import run_scraper

def main():
    parser = argparse.ArgumentParser(description="CarShop.com Inventory Scraper")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to scrape (default: 1)")
    parser.add_argument("--max-vehicles", type=int, default=None, help="Max vehicles to scrape (default: all)")
    parser.add_argument("--test", action="store_true", help="Test mode: scrape 1 page only")
    args = parser.parse_args()

    max_pages = 1 if args.test else args.pages
    max_vehicles = args.max_vehicles

    print(f"Starting CarShop scraper (pages: {max_pages}, max vehicles: {max_vehicles})...")
    try:
        vehicles_saved = run_scraper(max_pages=max_pages, max_vehicles=max_vehicles)
        print(f"Successfully scraped {vehicles_saved} vehicles")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
