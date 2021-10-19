from aiohttp import ClientSession

from process.items import get_tender_items
from process.profile import get_tender_profile
from process.shortlisted_firms import get_tender_shortlisted_firms

from utils import patch_tender


async def process_listing(session: ClientSession, tender: dict) -> None:
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

