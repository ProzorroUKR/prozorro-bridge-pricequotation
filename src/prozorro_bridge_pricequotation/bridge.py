import asyncio
import json
from aiohttp import ClientSession
from prozorro_bridge_pricequotation.process.profile import get_tender_profiles
from prozorro_bridge_pricequotation.process.items import get_tender_items
from prozorro_bridge_pricequotation.process.criteria import get_criteria
from prozorro_bridge_pricequotation.process.agreements import check_agreements
from prozorro_bridge_pricequotation.process.shortlisted_firms import get_tender_shortlisted_firms
from prozorro_bridge_pricequotation.settings import HEADERS, CDB_BASE_URL, LOGGER, ERROR_INTERVAL
from prozorro_bridge_pricequotation.utils import patch_tender, journal_context, check_tender
from prozorro_bridge_pricequotation.journal_msg_ids import (
    TENDER_EXCEPTION,
    TENDER_PATCHED,
)


async def get_tender(tender_id: str, session: ClientSession) -> dict:
    while True:
        try:
            response = await session.get(f"{CDB_BASE_URL}/tenders/{tender_id}", headers=HEADERS)
            data = await response.text()
            if response.status != 200:
                raise ConnectionError(f"Error {data}")
            LOGGER.warning(
                f"Get tender {tender_id}",
                extra=journal_context(
                    {"MESSAGE_ID": TENDER_EXCEPTION},
                    params={"TENDER_ID": tender_id}
                )
            )
            return json.loads(data)["data"]
        except Exception as e:
            LOGGER.warning(
                f"Fail to get tender {tender_id}",
                extra=journal_context(
                    {"MESSAGE_ID": TENDER_EXCEPTION},
                    params={"TENDER_ID": tender_id}
                )
            )
            LOGGER.exception(e)
            await asyncio.sleep(ERROR_INTERVAL)


async def process_listing(session: ClientSession, tender: dict) -> None:
    if not check_tender(tender):
        return None
    tender_id = tender["id"]
    tender = await get_tender(tender_id, session)

    profiles = await get_tender_profiles(tender, session)
    if not any(profiles):
        return None

    agreements = await check_agreements(tender, profiles, session)
    if not any(agreements):
        return None

    shortlisted_firms = await get_tender_shortlisted_firms(tender, session, agreements)
    if shortlisted_firms is None:
        return None

    status = "active.tendering"
    patch_data = {
        "data": {
            "shortlistedFirms": shortlisted_firms,
            "status": status
        }
    }

    if "profile" in tender:
        profile = profiles[0] or {}
        items = await get_tender_items(tender, profile)
        criteria = await get_criteria(profile.get("data", {}).get("criteria", []))
        patch_data["data"].update({
            "items": items,
            "criteria": criteria
        })

    is_patch = await patch_tender(tender_id, patch_data, session)
    if is_patch:
        LOGGER.info(
            f"Successfully patch tender {tender_id}",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_PATCHED},
                params={"TENDER_ID": tender_id},
            ),
        )
        return
    LOGGER.info(
        f"Unsuccessful patch tender {tender_id}",
        extra=journal_context(
            {"MESSAGE_ID": TENDER_EXCEPTION},
            params={"TENDER_ID": tender_id},
        ),
    )
    return


