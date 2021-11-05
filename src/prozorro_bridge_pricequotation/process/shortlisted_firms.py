from aiohttp import ClientSession
import json
from prozorro_bridge_pricequotation.journal_msg_ids import TENDER_EXCEPTION, AGREEMENTS_EXCEPTION
from prozorro_bridge_pricequotation.settings import LOGGER, CDB_BASE_URL
from prozorro_bridge_pricequotation.utils import journal_context, decline_resource


async def _get_tender_shortlisted_firms(tender: dict, session: ClientSession) -> list or None:
    tender_id = tender["id"]
    agreement_id = tender.get("agreement", {}).get("id")
    if not agreement_id:
        LOGGER.error(
            f"Agreement not found in tender {tender_id}",
            extra=journal_context(
                {"MESSAGE_ID": AGREEMENTS_EXCEPTION},
                params={"TENDER_ID": tender_id}
            )
        )
        return
    response = await session.get(f"{CDB_BASE_URL}/agreements/{agreement_id}")
    if response.status == 404:
        LOGGER.error(
            f"Agreement not found by agreement_id {agreement_id}",
            extra=journal_context(
                {"MESSAGE_ID": AGREEMENTS_EXCEPTION},
                params={"TENDER_ID": tender_id, "AGREEMENT_ID": agreement_id}
            )
        )
        return
    elif response.status != 200:
        LOGGER.error(
            f"Fail to get agreement by agreement_id {agreement_id}",
            extra=journal_context(
                {"MESSAGE_ID": AGREEMENTS_EXCEPTION},
                params={"TENDER_ID": tender_id, "AGREEMENT_ID": agreement_id}
            )
        )
        return
    else:
        shortlisted_firms = []
        agreements = json.loads(await response.text())
        agreements_data = agreements.get("data", {})
        for contract in agreements_data.get("contracts"):
            if contract.get("status") == "active":
                suppliers = contract.get("suppliers", [])
                if suppliers:
                    shortlisted_firms.append(contract.get("suppliers")[0])

        if not shortlisted_firms:
            LOGGER.error(
                f"This agreement {agreement_id} doesn`t have qualified suppliers",
                extra=journal_context(
                    {"MESSAGE_ID": AGREEMENTS_EXCEPTION},
                    params={"TENDER_ID": tender_id, "AGREEMENT_ID": agreement_id}
                )
            )
            reason = u"В обраних реєстрах немає активних постачальників"
            await decline_resource(tender_id, reason, session)
            return
    return shortlisted_firms


async def _get_tender_shortlisted_firms_by_agreement(tender: dict, session: ClientSession, agreements: list) -> list or None:
    tender_id = tender["id"]
    shortlisted_firms = []
    for agreement in agreements:
        for contract in agreement.get("contracts"):
            if contract.get("status") == "active":
                suppliers = contract.get("suppliers", [])
                if suppliers:
                    shortlisted_firms.append(contract.get("suppliers")[0])

    if not shortlisted_firms:
        LOGGER.error(
            f"This agreement {''} doesn`t have qualified suppliers",
        )
        reason = u"В обраних реєстрах немає активних постачальників"
        await decline_resource(tender_id, reason, session)
        return
    return shortlisted_firms


async def get_tender_shortlisted_firms(tender: dict, session: ClientSession, agreements: list) -> list or None:
    try:
        if not tender.get("agreement", {}).get("id"):
            return await _get_tender_shortlisted_firms_by_agreement(tender, session, agreements[0])
        return await _get_tender_shortlisted_firms(tender, session)
    except Exception as e:
        LOGGER.warn(
            "Fail to handle tender shortlisted_firms",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_EXCEPTION},
                params={"TENDER_ID": tender["id"]}
            )
        )
        LOGGER.exception(e)
        return
