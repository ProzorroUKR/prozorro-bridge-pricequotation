from aiohttp import ClientSession
from prozorro_bridge_pricequotation.journal_msg_ids import TENDER_SWITCHED, TENDER_NOT_SWITCHED, TENDER_INFO
from prozorro_bridge_pricequotation.settings import LOGGER, HEADERS, CDB_BASE_URL


def journal_context(record: dict = None, params: dict = None) -> dict:
    if record is None:
        record = {}
    if params is None:
        params = {}
    for k, v in params.items():
        record["JOURNAL_" + k] = v
    return record


async def patch_tender(tender_id: str, patch_data: dict, session: ClientSession) -> bool:
    url = "{}/tenders/{}".format(CDB_BASE_URL, tender_id)
    response = await session.patch(url, json=patch_data)
    if response.status != 200:
        return False
    else:
        return True


async def decline_resource(tender_id: str, reason: str,  session: ClientSession) -> dict or None:
    status = "draft.unsuccessful"
    patch_data = {"data": {"status": status, "unsuccessfulReason": [reason]}}
    is_patch = await patch_tender(tender_id, patch_data, session)
    if is_patch:
        LOGGER.info("Switch tender %s to `%s` with reason '%s'" % (tender_id, status, reason),
                    extra=journal_context(
                        {"MESSAGE_ID": TENDER_SWITCHED},
                        params={"TENDER_ID": tender_id, "STATUS": status})
                    )
    else:
        LOGGER.info("Not switch tender %s to `%s` with reason '%s'" % (tender_id, status, reason),
                    extra=journal_context(
                        {"MESSAGE_ID": TENDER_NOT_SWITCHED},
                        params={"TENDER_ID": tender_id, "STATUS": status})
                    )


def check_tender(tender: dict) -> bool:
    if tender["procurementMethodType"] == "priceQuotation" and tender["status"] == "draft.publishing":
        return True
    LOGGER.info(
        f"Skipping tender {tender['id']} in status {tender['status']} and procurementMethodType {tender['procurementMethodType']}",
        extra=journal_context(
            {"MESSAGE_ID": TENDER_INFO},
            params={"TENDER_ID": tender["id"]}
        ),
    )
    return False
