from aiohttp import ClientSession
import asyncio
import json
from prozorro_bridge_pricequotation.journal_msg_ids import TENDER_EXCEPTION, PROFILE_TO_SYNC, PROFILE_EXISTS
from prozorro_bridge_pricequotation.settings import LOGGER, CATALOG_BASE_URL, ERROR_INTERVAL, HEADERS
from prozorro_bridge_pricequotation.utils import journal_context, decline_resource


async def _get_tender_profile(tender: dict, session: ClientSession) -> dict or None:
    tender_id = tender['id']
    if "profile" not in tender:
        LOGGER.warning(
            f"No profile found in tender {tender_id}",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_EXCEPTION},
                {"TENDER_ID": tender["id"]}
            )
        )
        return
    profile_id = tender.get("profile")
    response = await session.get(f"{CATALOG_BASE_URL}/profiles/{profile_id}", headers=HEADERS)
    if response.status == 404:
        LOGGER.error("Profile {} not found in catalouges.".format(profile_id))
        reason = u"Обраний профіль не існує в системі Prozorro.Market"
        await decline_resource(tender_id, reason, session)
        return
    elif response.status != 200:
        LOGGER.info(
            f"Fail to profile existance {profile_id}.",
            extra=journal_context(
                {"MESSAGE_ID": PROFILE_TO_SYNC},
                {"PROFILE_ID": profile_id, "TENDER_ID": tender_id},
            ),
        )
        return
    else:
        LOGGER.info(
            f"Profile exists {profile_id}",
            extra=journal_context(
                {"MESSAGE_ID": PROFILE_EXISTS},
                {"TENDER_ID": tender_id, "PROFILE_ID": profile_id},
            ),
        )

        profile = json.loads(await response.text())
        profile_status = profile.get("data", {}).get("status")

        if profile_status == "general":
            LOGGER.error("Profile {} status '{}' is not available for publication, tender {}".format(profile_id,
                                                                                                     profile_status,
                                                                                                     tender_id))
            reason = u"Обраний профіль (загальний) недоступний для публікації закупівлі \"Запит ціни пропозиції\" в Prozorro.Market"
            await decline_resource(tender_id, reason, session)
            return

        if profile_status != "active":
            LOGGER.error("Profile {} status '{}' not equal 'active', tender {}".format(profile_id,
                                                                                       profile_status,
                                                                                       tender_id))
            reason = u"Обраний профіль неактивний в системі Prozorro.Market"
            await decline_resource(tender_id, reason, session)
            return

        return profile


async def get_tender_profile(tender: dict, session: ClientSession) -> dict or None:
    try:
        return await _get_tender_profile(tender, session)
    except Exception as e:
        LOGGER.warn(
            "Fail to handle tender profiles",
            extra=journal_context({"MESSAGE_ID": TENDER_EXCEPTION})
        )
        LOGGER.exception(e)
        return
