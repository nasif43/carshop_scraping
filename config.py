import random
import string

# Algolia Search API Configuration
ALGOLIA_APP_ID = "G58LKO3ETJ"
ALGOLIA_API_KEY = "cc3dce06acb2d9fc715bc10c9a624d80"
ALGOLIA_INDEX = "production-inventory-global_make_desc"
ALGOLIA_ENDPOINT = f"https://{ALGOLIA_APP_ID}-1.algolianet.com/1/indexes/{ALGOLIA_INDEX}/query"

ALGOLIA_HEADERS = {
    "Origin": "https://carshop.com",
    "Referer": "https://carshop.com/",
    "x-algolia-agent": "Algolia for JavaScript (4.18.0); Browser (lite)",
    "x-algolia-api-key": ALGOLIA_API_KEY,
    "x-algolia-application-id": ALGOLIA_APP_ID,
    "Content-Type": "application/json",
}

ALGOLIA_HITS_PER_PAGE = 36
ALGOLIA_CACHE_DIR = "algolia_cache"
ALGOLIA_FILTERS = (
    "is_active:true AND dealer_ids:\"429\" AND "
    "dealership:\"CarShop Hatfield\"<score=3> OR "
    "dealership:\"CarShop Cranberry\"<score=1> OR "
    "dealership:\"CarShop Chester Springs\"<score=2> OR "
    "dealership:\"CarShop Glen Mills\"<score=2> OR "
    "dealership:\"CarShop Mount Holly\"<score=2> OR "
    "dealership:\"CarShop Robinson\"<score=1>"
)

def generate_user_token(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Impel Vehicle Details API Configuration
IMPEL_BASE_URL = "https://api.impel.io/spin/carsenserobinsontwp"
IMPEL_HEADERS = {
    "Origin": "https://embed.spincar.com",
    "Referer": "https://embed.spincar.com/",
    "Accept": "*/*",
}

# RideMotive Vehicle Details API Configuration
RIDEMOTIVE_BASE_URL = "https://api.app.ridemotive.com/vehicles"
RIDEMOTIVE_HEADERS = {
    "Origin": "https://carshop.com",
    "Referer": "https://carshop.com/",
    "Accept": "application/json",
}

# Algolia Image CDN Prefix (confirmed from browser)
ALGOLIA_IMAGE_CDN_PREFIX = "https://images.app.ridemotive.com"

# Impel CDN Prefix (confirmed from browser)
IMPEL_CDN_PREFIX = "https://cdn.impel.io/swipetospin-viewers/carsenserobinsontwp"
IMPEL_S3_FOLDER = "carsenserobinsontwp"
IMPEL_S3_PREFIX = "s3://swipetospin-viewers/carsenserobinsontwp"

# Scraper Settings
DELAY_MIN = 2
DELAY_MAX = 5

# Database Configuration
SQLITE_DB = "carshop_scraper.db"

# Output Configuration
OUTPUT_FILE = "carshop_inventory.jsonl"
