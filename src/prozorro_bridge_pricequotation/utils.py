from aiohttp import ClientSession
from prozorro_crawler.settings import (
    API_VERSION,
    CRAWLER_USER_AGENT,
)

from prozorro_bridge_pricequotation.journal_msg_ids import (
    TENDER_SWITCHED,
    TENDER_NOT_SWITCHED,
    TENDER_INFO,
)
from prozorro_bridge_pricequotation.settings import (
    LOGGER,
    API_HOST,
    API_TOKEN,
    CATALOG_API_HOST,
    JOURNAL_PREFIX,
)

BASE_URL = f"{API_HOST}/api/{API_VERSION}"
CATALOG_BASE_URL = f"{CATALOG_API_HOST}/api"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}",
    "User-Agent": CRAWLER_USER_AGENT,
}

CATALOGUE_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "",
    "User-Agent": CRAWLER_USER_AGENT,
}


def journal_context(record: dict = None, params: dict = None) -> dict:
    if record is None:
        record = {}
    if params is None:
        params = {}
    for k, v in params.items():
        record[JOURNAL_PREFIX + k] = v
    return record


async def patch_tender(tender_id: str, patch_data: dict, session: ClientSession) -> bool:
    url = "{}/tenders/{}".format(BASE_URL, tender_id)
    response = await session.patch(url, json=patch_data, headers=HEADERS)
    if response.status != 200:
        return False
    else:
        return True


async def decline_resource(tender_id: str, reason: str, session: ClientSession) -> dict or None:
    status = "draft.unsuccessful"
    patch_data = {"data": {"status": status, "unsuccessfulReason": [reason]}}
    is_patch = await patch_tender(tender_id, patch_data, session)
    if is_patch:
        LOGGER.info(
            f"Switch tender {tender_id} to {status} with reason: {reason}",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_SWITCHED},
                params={"TENDER_ID": tender_id, "STATUS": status}
            )
        )
    else:
        LOGGER.info(
            f"Not switch tender {tender_id} to {status} with reason: {reason}",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_NOT_SWITCHED},
                params={"TENDER_ID": tender_id, "STATUS": status}
            )
        )


def check_tender(tender: dict) -> bool:
    tender_procurementMethodType = tender.get("procurementMethodType")
    tender_status = tender.get("status")
    tender_id = tender.get("id")
    if tender_procurementMethodType == "priceQuotation" and tender_status == "draft.publishing":
        return True
    LOGGER.debug(
        f"Skipping tender {tender_id} in status {tender_status} "
        f"and procurementMethodType {tender_procurementMethodType}",
        extra=journal_context(
            {"MESSAGE_ID": TENDER_INFO},
            params={"TENDER_ID": tender_id}
        ),
    )
    return False
