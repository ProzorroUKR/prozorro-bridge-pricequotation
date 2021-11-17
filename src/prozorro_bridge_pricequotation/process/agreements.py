import asyncio
from aiohttp import ClientSession
import json
from prozorro_bridge_pricequotation.journal_msg_ids import AGREEMENTS_EXISTS, AGREEMENTS_EXCEPTION, PROFILE_EXCEPTION
from prozorro_bridge_pricequotation.settings import LOGGER, CDB_BASE_URL
from prozorro_bridge_pricequotation.utils import journal_context, decline_resource


async def find_agreements_by_classification_id(classification_id: str, additional_classifications_ids: list, session: ClientSession, tender_id: str) -> list or None:
    url = "{}/agreements_by_classification/{}".format(CDB_BASE_URL, classification_id)
    params = {}
    if additional_classifications_ids:
        params["additional_classifications"] = ",".join(additional_classifications_ids)
    response = await session.get(url, params=params)
    if response.status == 200:
        resource_items_list = json.loads(await response.text())
        LOGGER.error(
            f"Get agreements by classification {classification_id}",
            extra=journal_context(
                {"MESSAGE_ID": AGREEMENTS_EXISTS},
                params={"TENDER_ID": tender_id}
            )
        )
        return resource_items_list.get("data", [])
    LOGGER.error(
        f"Fail to get agreements by classification {classification_id}",
        extra=journal_context(
            {"MESSAGE_ID": AGREEMENTS_EXCEPTION},
            params={"TENDER_ID": tender_id}
        )
    )
    return


async def find_recursive_agreements_by_classification_id(classification_id: str, additional_classifications_ids: list, session: ClientSession, tender_id: str) -> list or None:
    if "-" in classification_id:
        classification_id = classification_id[:classification_id.find("-")]
    needed_level = 2
    while classification_id[needed_level] != '0':
        agreements = await find_agreements_by_classification_id(classification_id, additional_classifications_ids, session, tender_id)
        if agreements:
            return agreements

        pos = classification_id[1:].find('0')
        classification_id = classification_id[:pos] + '0' + classification_id[pos + 1:]
        await asyncio.sleep(1)
    return


async def _old_check_agreements(tender: dict, profile: dict, session: ClientSession) -> list:
    tender_id = tender["id"]
    tender_date_modified = tender['dateModified']
    classification_id = profile.get("data", {}).get("classification", {}).get("id")
    additional_classifications = profile.get("data", {}).get("additionalClassifications", [])
    additional_classifications_ids = []
    for i in additional_classifications:
        if additional_classifications:
            additional_classifications_ids.append(i.get("id"))
        continue

    agreements = await find_recursive_agreements_by_classification_id(classification_id, additional_classifications_ids, session, tender_id)

    if not agreements:
        LOGGER.error(
            "There are no any active agreement for classification: {} or for levels higher".format(classification_id)
        )
        reason = u"Для обраного профілю немає активних реєстрів"
        await decline_resource(tender_id, reason, session, tender_date_modified)
        return []
    return agreements


async def _new_check_agreements(tender: dict, profile: dict, session: ClientSession) -> list:
    tender_id = tender["id"]
    tender_date_modified = tender['dateModified']
    profile_agreement_id = profile.get("data", {}).get("agreementID")
    tender_agreement_id = tender.get("agreement", {}).get("id")
    if profile_agreement_id != tender_agreement_id:
        LOGGER.error(
            "There are no any active agreement by {}".format(tender_agreement_id)
        )
        reason = u"Для обраного профілю немає активних реєстрів"
        await decline_resource(tender_id, reason, session, tender_date_modified)
        return []
    return [True]


async def check_agreements(tender: dict, profiles: list, session: ClientSession) -> list:
    tender_id = tender["id"]
    try:
        agreements = []
        _check_agreements = _old_check_agreements
        if tender.get("agreement", {}).get("id"):
            _check_agreements = _new_check_agreements
        for profile in profiles:
            agreement = await _check_agreements(tender, profile, session)
            if not agreement:
                return []
            agreements.append(agreement)
        return agreements
    except Exception as e:
        LOGGER.warn(
            "Fail to handle tender profiles",
            extra=journal_context(
                {"MESSAGE_ID": PROFILE_EXCEPTION},
                params={"TENDER_ID": tender_id}
            )
        )
        LOGGER.exception(e)
        return []
