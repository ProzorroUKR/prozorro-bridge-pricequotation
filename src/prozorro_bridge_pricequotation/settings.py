import os
from prozorro_crawler.settings import logger


MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://root:example@localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "prozorro-bridge-pricequotation")
MONGODB_CONTRACTS_COLLECTION = os.environ.get("MONGODB_CONTRACTS_COLLECTION", "pricequotation")
ERROR_INTERVAL = int(os.environ.get("ERROR_INTERVAL", 5))

CDB_PUBLIC_API_HOST = os.environ.get("CDB_PUBLIC_API_HOST", "https://lb-api-sandbox-2.prozorro.gov.ua")
CDB_API_VERSION = os.environ.get("CDB_API_VERSION", "2.5")
CDB_BASE_URL = f"{CDB_PUBLIC_API_HOST}/api/{CDB_API_VERSION}"

CATALOG_API_HOST = os.environ.get("PUBLIC_API_HOST", "https://catalog-test.prozorro.ua")
CATALOG_API_VERSION = os.environ.get("CATALOG_API_VERSION", "0")
CATALOG_BASE_URL = f"{CATALOG_API_HOST}/api/{CDB_API_VERSION}"


API_TOKEN = os.environ.get("API_TOKEN", "pqbot")
USER_AGENT = os.environ.get("USER_AGENT", "priceQuotationBot")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}",
    "User-Agent": USER_AGENT,
}

LOGGER = logger
