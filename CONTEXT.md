# CarShop.com Scraper Project Context
## Last Updated: 2026-05-05
## Project Overview
- **Goal:** Scrape carshop.com for: car name, first image URL, full features/specs
- **Data Pipeline:** Algolia Search API (listing previews) + Impel API (extended vehicle details)
- **Anti-bot strategy:** curl_cffi (Chrome impersonation), rotating user agents, 2-5s random delays, optional residential proxies
- **Deduplication:** SQLite tracking (VIN, listing URL, title+price+mileage fingerprint)
- **Output:** JSON Lines format (one JSON object per listing)

## Environment Setup
- Python 3.13.5
- Virtual env: `env/` (activate with `source env/bin/activate`)
- Confirmed installed packages: `curl_cffi`, `beautifulsoup4`, `lxml`
- Removed unnecessary packages: `pandas`, `sqlalchemy` (not needed for core scraper)

## Progress & Milestones
- [x] Researched carshop.com structure (Algolia API, Impel API, RideMotive API)
- [x] Identified Algolia configuration (app ID, API key, index, endpoint)
- [x] Identified Impel API endpoint for vehicle details (case-sensitive VIN)
- [x] Confirmed 36 vehicles per Algolia page (matches scroll behavior)
- [x] Confirmed Impel CDN prefix: https://cdn.impel.io/swipetospin-viewers/carsenserobinsontwp
- [x] Identified RideMotive API for vehicle_details (using vehicle_id from Algolia)
- [x] Algolia image CDN prefix: https://images.app.ridemotive.com/{key} ✅
- [x] Phase1: Create core files (config.py, database.py, utils.py, parsers.py, scraper.py, main.py)
- [x] Phase2: Test 1-page Algolia scrape - Algolia parsing works ✅
- [x] Phase3: Test Impel API (thumb image) + RideMotive API (engine specs) - both working ✅
- [x] Phase4: Validate SQLite deduplication - working ✅
- [x] Phase5: End-to-end test with 2 vehicles - success ✅
- [x] Phase6: Implement anti-bot measures (delays, retries, Chrome rotation) ✅
- [x] Phase7: Fix all bugs (DELAY_MIN/MAX, LONG_BREAK_INTERVAL, listing_url removal) ✅
- [ ] Phase8: Full scrape (41 pages, ~1442 vehicles)

## Blockers
- [x] Image CDN prefix for Algolia `images` keys: https://images.app.ridemotive.com/{key} ✅
- [x] RideMotive API works with vehicle_id from Algolia `id` field ✅
- [x] Impel API works for image fallback (thumb field, requires lowercase VIN) ✅

## Anti-Bot Strategy (Implemented)
- [x] Chrome impersonation via curl_cffi (rotating between chrome110, chrome120, chrome123)
- [x] Random delays (2-5s + jitter) between requests
- [x] Retry logic with exponential backoff for 429/403/timeouts
- [x] Periodic longer breaks (30-60s every 10 vehicles)
- [x] Pagination delays (random 2-5s between Algolia pages)
- [ ] Proxy rotation (no proxies available - skipped)

## Next Steps (Current Session)
1. Update CONTEXT.md ✅
2. Create project files in order: config.py → database.py → utils.py → parsers.py → scraper.py → main.py ✅
3. Test 1-page scrape ✅
4. Validate dedup and data extraction ✅
5. Implement anti-bot measures ✅
6. Fix all bugs (DELAY_MIN/MAX, LONG_BREAK_INTERVAL, listing_url removal) ✅
7. Ready for full scrape (41 pages, ~1442 vehicles) ✅
8. Created concurrent version (scraper_concurrent.py) for speed testing on VPS ✅

## Critical Workflow Rule
**ALWAYS read this file first when starting work in this directory:**
```bash
read /mnt/d/Work/nexvix/cars.com_scraping/CONTEXT.md
```
Update this file after every session with progress, blockers, and next steps.

## API Configuration
### Algolia Search API
- Application ID: `G58LKO3ETJ`
- Public API Key: `cc3dce06acb2d9fc715bc10c9a624d80`
- Index Name: `production-inventory-global_make_desc`
- Endpoint: `POST https://g58lko3etj-1.algolianet.com/1/indexes/production-inventory-global_make_desc/query`
- Request Body Params: `query`, `clickAnalytics`, `userToken`, `filters`, `page`, `hitsPerPage=36`
- Required Headers: `Origin: https://carshop.com`, `Referer: https://carshop.com/`, `x-algolia-agent: Algolia for JavaScript (4.18.0); Browser (lite)`

### Impel Vehicle Details API
- Endpoint: `GET https://api.impel.io/spin/carsenserobinsontwp/{vin}`
- Required Headers: `Origin: https://embed.spincar.com`, `Referer: https://embed.spincar.com/`
- Response: `vehicle_details` object with engine specs, standard equipment, EPA efficiency

## Test URLs
- Inventory Page: `https://carshop.com/inventory`
- Algolia Query: `POST https://g58lko3etj-1.algolianet.com/1/indexes/production-inventory-global_make_desc/query`
- Impel Detail: `GET https://api.impel.io/spin/carsenserobinsontwp/3GKALTEV1KL290793`

## Notes
- Algolia returns 36 vehicles per page (matches scroll-to-load behavior)
- Use VIN (17-char) from Algolia results for Impel API calls (not internal `id`)
- Image keys in Algolia `images` array need CDN prefix to resolve full URLs (to confirm)
- Start with 1 page (36 vehicles) before scaling to full pagination
