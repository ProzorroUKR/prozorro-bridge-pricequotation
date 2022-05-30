from aiohttp import ClientSession
import json
from prozorro_bridge_pricequotation.journal_msg_ids import TENDER_EXCEPTION, PROFILE_TO_SYNC, PROFILE_EXISTS
from prozorro_bridge_pricequotation.settings import LOGGER
from prozorro_bridge_pricequotation.utils import journal_context, decline_resource, CATALOG_BASE_URL, CATALOGUE_HEADERS


async def _get_tender_profile(tender: dict, session: ClientSession, profile_id: str) -> dict or None:
    tender_id = tender['id']
    response = await session.get(f"{CATALOG_BASE_URL}/profiles/{profile_id}", headers=CATALOGUE_HEADERS)
    if response.status == 404:
        LOGGER.error(f"Profile {profile_id} not found in catalouges.")
        reason = u"Обраний профіль не існує в системі Prozorro.Market"
        await decline_resource(tender_id, reason, session)
        return
    elif response.status != 200:
        response_text = await response.text()
        LOGGER.info(
            f"Fail to profile existance {profile_id}: {response.status} {response_text}.",
            extra=journal_context(
                {"MESSAGE_ID": PROFILE_TO_SYNC},
                params={"PROFILE_ID": profile_id, "TENDER_ID": tender_id},
            ),
        )
        return
    else:
        LOGGER.info(
            f"Profile exists {profile_id}",
            extra=journal_context(
                {"MESSAGE_ID": PROFILE_EXISTS},
                params={"TENDER_ID": tender_id, "PROFILE_ID": profile_id},
            ),
        )

        profile = json.loads(await response.text())
        profile_status = profile.get("data", {}).get("status")

        if profile_status == "general":
            LOGGER.error(f"Profile {profile_id} status '{profile_status}' is not available for publication, tender {tender_id}")
            reason = u"Обраний профіль (загальний) недоступний для публікації закупівлі \"Запит ціни пропозиції\" в Prozorro.Market"
            await decline_resource(tender_id, reason, session)
            return

        if profile_status != "active":
            LOGGER.error(f"Profile {profile_id} status '{profile_status}' not equal 'active', tender {tender_id}")
            reason = u"Обраний профіль неактивний в системі Prozorro.Market"
            await decline_resource(tender_id, reason, session)
            return

        return profile


async def _get_tender_profiles_ids(tender: dict) -> list or None:
    profile_ids = []
    if "profile" in tender:
        profile_ids = [tender["profile"]]
    else:
        for items in tender.get("items", []):
            profile_id = items.get("profile")
            if profile_id:
                profile_ids.append(profile_id)
    return profile_ids


async def get_tender_profiles(tender: dict, session: ClientSession) -> list:
    tender_id = tender["id"]
    try:
        profile_ids = await _get_tender_profiles_ids(tender)
        if len(profile_ids) == 0:
            LOGGER.warning(
                f"Profiles not found in tender {tender_id}",
                extra=journal_context(
                    {"MESSAGE_ID": TENDER_EXCEPTION},
                    params={"TENDER_ID": tender_id}
                )
            )
            return []

        profiles = []
        for profile_id in profile_ids:
            profile = await _get_tender_profile(tender, session, profile_id)
            if profile is None:
                return []
            profiles.append(profile)
        return profiles
    except Exception as e:
        LOGGER.warn(
            "Fail to handle tender profiles",
            extra=journal_context(
                {"MESSAGE_ID": TENDER_EXCEPTION},
                params={"TENDER_ID": tender_id}
            )
        )
        LOGGER.exception(e)
        return []
