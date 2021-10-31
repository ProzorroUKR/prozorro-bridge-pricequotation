from aiohttp import ClientSession
import json
from prozorro_bridge_pricequotation.journal_msg_ids import TENDER_EXCEPTION
from prozorro_bridge_pricequotation.settings import LOGGER, ERROR_INTERVAL, CDB_BASE_URL, HEADERS
from prozorro_bridge_pricequotation.utils import journal_context, decline_resource


async def find_agreements_by_classification_id(classification_id: str, additional_classifications_ids: list, session: ClientSession) -> dict or None:
    url = "{}/agreements_by_classification/{}".format(CDB_BASE_URL, classification_id)
    params = {}
    if additional_classifications_ids:
        params["additional_classifications"] = ",".join(additional_classifications_ids)
    response = await session.get(url, headers=HEADERS, params=params)
    if response.status == 200:
        resource_items_list = json.loads(await response.text())
        return resource_items_list.get("data", {})
    return


async def find_recursive_agreements_by_classification_id(classification_id: str, additional_classifications_ids: list, session: ClientSession) -> dict or None:
    if "-" in classification_id:
        classification_id = classification_id[:classification_id.find("-")]
    needed_level = 2
    while classification_id[needed_level] != '0':
        agreements = await find_agreements_by_classification_id(classification_id, additional_classifications_ids, session)
        if agreements:
            return agreements

        pos = classification_id[1:].find('0')
        classification_id = classification_id[:pos] + '0' + classification_id[pos + 1:]


async def _get_tender_shortlisted_firms(tender: dict, profile: dict, session: ClientSession) -> list or None:
    tender_id = tender["id"]
    classification_id = profile.get("data", {}).get("classification", {}).get("id")
    additional_classifications = profile.get("data", {}).get("additionalClassifications", [])
    additional_classifications_ids = []
    for i in additional_classifications:
        if additional_classifications:
            additional_classifications_ids.append(i.get("id"))
        continue

    agreements = await find_recursive_agreements_by_classification_id(classification_id, additional_classifications_ids, session)

    if not agreements:
        LOGGER.error(
            "There are no any active agreement for classification: {} or for levels higher".format(classification_id)
        )
        reason = u"Для обраного профілю немає активних реєстрів"
        await decline_resource(tender_id, reason, session)
        return

    shortlisted_firms = []

    for agreement in agreements:
        for contract in agreement.get("contracts"):
            if contract.get("status") == "active":
                suppliers = contract.get("suppliers", [])
                if suppliers:
                    shortlisted_firms.append(contract.get("suppliers")[0])

    shortlisted_firms = shortlisted_firms

    if not shortlisted_firms:
        LOGGER.error(
            "This category {} doesn`t have qualified suppliers".format(profile.get("data", {}).get("relatedCategory"))
        )
        reason = u"В обраних реєстрах немає активних постачальників"
        await decline_resource(tender_id, reason, session)
        return
    return shortlisted_firms


async def get_tender_shortlisted_firms(tender: dict, profile: dict, session: ClientSession) -> list or None:
    try:
        return await _get_tender_shortlisted_firms(tender, profile, session)
    except Exception as e:
        LOGGER.warn(
            "Fail to handle tender shortlisted_firms",
            extra=journal_context({"MESSAGE_ID": TENDER_EXCEPTION})
        )
        LOGGER.exception(e)
        return
