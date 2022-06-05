import os
from prozorro_crawler.settings import logger, PUBLIC_API_HOST


LOGGER = logger

API_HOST = os.environ.get("API_HOST", PUBLIC_API_HOST)
API_OPT_FIELDS = os.environ.get("API_OPT_FIELDS", "status,procurementMethodType")
API_TOKEN = os.environ.get("API_TOKEN", "pqBot")

ERROR_INTERVAL = int(os.environ.get("ERROR_INTERVAL", 5))

JOURNAL_PREFIX = os.environ.get("JOURNAL_PREFIX", "JOURNAL_")

CATALOG_API_HOST = os.environ.get("CATALOG_API_HOST", "https://catalog-api-sandbox-2.prozorro.gov.ua")

SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
