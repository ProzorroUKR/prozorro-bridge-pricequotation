import asyncio
import json
from aiohttp import ClientSession
from prozorro_bridge_pricequotation.process.items import get_tender_items
from prozorro_bridge_pricequotation.process.profile import get_tender_profile
from prozorro_bridge_pricequotation.process.shortlisted_firms import get_tender_shortlisted_firms
from prozorro_bridge_pricequotation.settings import HEADERS, CDB_BASE_URL, LOGGER, ERROR_INTERVAL
from prozorro_bridge_pricequotation.utils import patch_tender, journal_context, check_tender
from prozorro_bridge_pricequotation.db import Db
from prozorro_bridge_pricequotation.journal_msg_ids import (
    TENDER_EXCEPTION,
    TENDER_PATCHED,
)

cache_db = Db()


async def check_cache(tender: dict) -> bool:
    return await cache_db.has_tender(tender["id"])


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
    tender = await get_tender(tender["id"], session)

    profile = await get_tender_profile(tender, session)
    if profile is None:
        return None

    shortlisted_firms = await get_tender_shortlisted_firms(tender, profile, session)
    if shortlisted_firms is None:
        return None

    items = await get_tender_items(tender, profile)
    if items is None:
        return None

    status = "active.tendering"
    data = {
        "data": {
            "criteria": profile.get("data", {}).get("criteria"),
            "items": items,
            "shortlistedFirms": shortlisted_firms,
            "status": status
        }
    }
    is_patch = await patch_tender(tender["id"], data, session)
    if is_patch:
        LOGGER.info(
            f"Successfully patch tender {tender['id']}",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_PATCHED},
                {"TENDER_ID": tender["id"]},
            ),
        )
        return
    LOGGER.info(
        f"Unsuccessful patch tender {tender['id']}",
        extra=journal_context(
            {"MESSAGE_ID": TENDER_EXCEPTION},
            {"TENDER_ID": tender["id"]},
        ),
    )
    return


