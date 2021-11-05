import copy
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from prozorro_bridge_pricequotation.bridge import (
    get_tender,
    process_listing,
)
from prozorro_bridge_pricequotation.process.profile import get_tender_profiles
from prozorro_bridge_pricequotation.process.shortlisted_firms import get_tender_shortlisted_firms
from prozorro_bridge_pricequotation.utils import check_tender
from base import TEST_TENDER, TEST_PROFILE, TEST_AGREEMENT


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_check_tender_is_not_valid(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    tender_data["data"]["procurementMethodType"] = "test"
    is_check = check_tender(tender_data["data"])
    assert is_check is False


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_check_tender_is_valid(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    is_check = check_tender(tender_data["data"])
    assert is_check is True


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_process_listing(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
    agreement_data = copy.deepcopy(TEST_AGREEMENT)

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


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_shortlisted_firms_if_contract_is_not_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    agreement_data = copy.deepcopy(TEST_AGREEMENT)
    for agreement in agreement_data.get('data'):
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
async def test_get_shortlisted_firms_if_contract_is_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    agreement_data = copy.deepcopy(TEST_AGREEMENT)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        shortlisted_firms = await get_tender_shortlisted_firms(tender_data["data"], session_mock, [agreement_data["data"]])
    shortlisted_firms_test = []
    for agreement in agreement_data.get('data'):
        for contract in agreement.get("contracts"):
            if contract.get("status") == "active":
                suppliers = contract.get("suppliers", [])
                if suppliers:
                    shortlisted_firms_test.append(contract.get("suppliers")[0])

    assert shortlisted_firms_test == shortlisted_firms


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_profile_if_status_is_general(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
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
async def test_get_profile_if_status_is_not_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
    profile_data["data"]["status"] = "not_active"
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
async def test_get_profile_if_status_is_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
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
async def test_get_tender(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=410, text=AsyncMock(return_value=json.dumps({"status": "error"}))),
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps({"data": tender_data}))),
        ]
    )

    fid_data = {
        "id": tender_data["data"]["id"],
        "status": tender_data["data"]["status"],
        "procurementMethodType": tender_data["data"]["procurementMethodType"]
    }
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        tender = await get_tender(fid_data["id"], session_mock)

    assert mocked_logger.exception.call_count == 1
    assert mocked_sleep.await_count == 1
    assert session_mock.get.await_count == 2
    assert tender_data == tender
