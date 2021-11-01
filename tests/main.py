import copy
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from prozorro_bridge_pricequotation.bridge import (
    get_tender,
    process_listing,
)
from prozorro_bridge_pricequotation.process.profile import get_tender_profile
from prozorro_bridge_pricequotation.process.shortlisted_firms import get_tender_shortlisted_firms
from prozorro_bridge_pricequotation.process.items import get_tender_items
from base import TEST_TENDER, TEST_PROFILE, TEST_AGREEMENT


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_process_listing(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
    agreement_data = copy.deepcopy(TEST_AGREEMENT)

    db_mock = AsyncMock()
    db_mock.has_tender = AsyncMock(return_value=False)

    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps({"data": tender_data}))),
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(profile_data))),
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    session_mock.patch = AsyncMock(
        side_effect=[
            MagicMock(status=200),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.cache_db", AsyncMock()) as mocked_sleep:
        await process_listing(session_mock, tender_data["data"])
    assert session_mock.post.await_count == 0


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_tender_items(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)

    items_data = [
        {
            'description': 'Добрі монітори, добродіям',
            'deliveryAddress': {
                'countryName': 'Україна',
                'region': 'Тернопільська область'
            },
            'deliveryDate': {
                'endDate': '2019-08-24T00:00:00+03:00'
            },
            'id': 'f6639e3ca222426d9a71c29b90fd5bce',
            'quantity': 4.0,
            'additionalClassifications': [
                {
                    'description': 'Enoxaparin',
                    'id': 'enoxaparin',
                    'scheme': 'INN'
                },
                {
                    'description': 'B01AB05',
                    'id': 'B01AB05',
                    'scheme': 'ATC'
                }
            ],
            'unit': {
                'code': 'H87',
                'name': 'штук'
            },
            'classification': {
                'description': 'Комп’ютерне обладнанн',
                'id': '30230000-0',
                'scheme': 'ДК021'
            }
        }
    ]
    items = await get_tender_items(tender_data["data"], profile_data)
    assert items_data == items


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_shortlisted_firms_if_contract_is_not_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
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
        shortlisted_firms = await get_tender_shortlisted_firms(tender_data["data"], profile_data, session_mock)
    assert shortlisted_firms is None


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_shortlisted_firms_if_contract_is_active(mocked_logger):
    tender_data = copy.deepcopy(TEST_TENDER)
    profile_data = copy.deepcopy(TEST_PROFILE)
    agreement_data = copy.deepcopy(TEST_AGREEMENT)
    session_mock = AsyncMock()
    session_mock.get = AsyncMock(
        side_effect=[
            MagicMock(status=200, text=AsyncMock(return_value=json.dumps(agreement_data))),
        ]
    )
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        shortlisted_firms = await get_tender_shortlisted_firms(tender_data["data"], profile_data, session_mock)
    shortlisted_firms_test = []
    for agreement in agreement_data.get('data'):
        for contract in agreement.get("contracts"):
            if contract.get("status") == "active":
                suppliers = contract.get("suppliers", [])
                if suppliers:
                    shortlisted_firms_test.append(contract.get("suppliers")[0])

    shortlisted_firms_test = shortlisted_firms_test
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
        profile = await get_tender_profile(tender_data["data"], session_mock)

    assert profile is None


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
        profile = await get_tender_profile(tender_data["data"], session_mock)

    assert profile is None


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
        profile = await get_tender_profile(tender_data["data"], session_mock)

    assert profile_data == profile


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
    with patch("prozorro_bridge_pricequotation.bridge.asyncio.sleep", AsyncMock()) as mocked_sleep:
        tender = await get_tender(tender_data["data"]["id"], session_mock)

    assert mocked_logger.exception.call_count == 1
    assert mocked_sleep.await_count == 1
    assert session_mock.get.await_count == 2
    assert tender_data == tender



