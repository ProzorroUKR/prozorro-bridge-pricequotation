import copy
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from prozorro_bridge_pricequotation.bridge import (
    process_listing,
)
from prozorro_bridge_pricequotation.process.profile import get_tender_profiles
from prozorro_bridge_pricequotation.process.shortlisted_firms import get_tender_shortlisted_firms
from prozorro_bridge_pricequotation.process.agreements import check_agreements
from base import TEST_NEW_TENDER, TEST_NEW_AGREEMENT, TEST_NEW_PROFILE


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_check_new_agreements_is_not_valid(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    profile_data["data"]["agreementID"] = ""
    session_mock = AsyncMock()

    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        agreements = await check_agreements(tender_data["data"], [profile_data], session_mock)

    assert [] == agreements


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_check_new_agreements_is_valid(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    session_mock = AsyncMock()

    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        agreements = await check_agreements(tender_data["data"], [profile_data], session_mock)

    assert [[True]] == agreements


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_new_shortlisted_firms_if_contract_is_not_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    agreement_data = copy.deepcopy(TEST_NEW_AGREEMENT)
    agreement = agreement_data.get('data', {})
    for contract in agreement.get("contracts"):
        contract["status"] = "not active"
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        shortlisted_firms = await get_tender_shortlisted_firms(tender_data["data"], session_mock, [agreement_data["data"]])
    assert shortlisted_firms is None


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_new_shortlisted_firms_if_contract_is_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    agreement_data = copy.deepcopy(TEST_NEW_AGREEMENT)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        shortlisted_firms = await get_tender_shortlisted_firms(tender_data["data"], session_mock, [agreement_data["data"]])
    shortlisted_firms_test = []
    agreement = agreement_data.get('data', {})
    for contract in agreement.get("contracts"):
        if contract.get("status") == "active":
            suppliers = contract.get("suppliers", [])
            if suppliers:
                shortlisted_firms_test.append(contract.get("suppliers")[0])

    assert shortlisted_firms_test == shortlisted_firms


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_new_profile_if_status_is_not_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(profile_data))),
        ]
    )
    session_mock.patch = AsyncMock(
        side_effect=[
            MagicMock(status=200),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        profile = await get_tender_profiles(tender_data["data"], session_mock)

    assert [profile_data] == profile



@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_new_profile_if_status_is_general(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    profile_data["data"]["status"] = "general"
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(profile_data))),
        ]
    )
    session_mock.patch = AsyncMock(
        side_effect=[
            MagicMock(status=200),
        ]
    )

    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        profile = await get_tender_profiles(tender_data["data"], session_mock)

    assert profile == []

@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_new_profile_if_status_is_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(profile_data))),
        ]
    )
    session_mock.patch = AsyncMock(
        side_effect=[
            MagicMock(status=200),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        profile = await get_tender_profiles(tender_data["data"], session_mock)

    assert [profile_data] == profile


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_new_process_listing(mocked_logger):
    tender_data = copy.deepcopy(TEST_NEW_TENDER)
    profile_data = copy.deepcopy(TEST_NEW_PROFILE)
    agreement_data = copy.deepcopy(TEST_NEW_AGREEMENT)

    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(tender_data))),
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(profile_data))),
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    session_mock.patch = AsyncMock(
        side_effect=[
            MagicMock(status=200),
        ]
    )

    fid_data = {
        "id": tender_data["data"]["id"],
        "status": tender_data["data"]["status"],
        "procurementMethodType": tender_data["data"]["procurementMethodType"]
    }
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        await process_listing(session_mock, fid_data)

    assert session_mock.post.await_count == 0
    assert session_mock.get.await_count == 3
    assert session_mock.patch.await_count == 1
