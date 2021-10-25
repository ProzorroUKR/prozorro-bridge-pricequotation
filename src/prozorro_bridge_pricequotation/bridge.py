import asyncio
import json
from aiohttp import ClientSession
from process.items import get_tender_items
from process.profile import get_tender_profile
from process.shortlisted_firms import get_tender_shortlisted_firms
from settings import HEADERS, CDB_BASE_URL, LOGGER, ERROR_INTERVAL
from utils import patch_tender, journal_context
from db import Db
from journal_msg_ids import TENDER_EXCEPTION

cache_db = Db()


async def get_tender(tender_id: str, session: ClientSession) -> dict:
    while True:
        try:
            response = await session.get(f"{CDB_BASE_URL}/tenders/{tender_id}", headers=HEADERS)
            data = await response.text()
            if response.status != 200:
                raise ConnectionError(f"Error {data}")
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
    tender = await get_tender(tender["id"], session)
    profile = await get_tender_profile(tender, session)
    shortlisted_firms = await get_tender_shortlisted_firms(tender, profile, session)
    items = await get_tender_items(tender, session)

    status = "active.tendering"
    data = {
        "data": {
            "criteria": profile.get("data", {}).get("criteria"),
            "items": items,
            "shortlistedFirms": shortlisted_firms,
            "status": status
        }
    }
    await patch_tender(tender["id"], data, session)

