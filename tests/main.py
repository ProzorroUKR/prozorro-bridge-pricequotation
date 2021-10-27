import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from prozorro_bridge_pricequotation.bridge import (
    get_tender,
)
from base import TEST_TENDER


@pytest.mark.asyncio
@patch("prozorro_bridge_pricequotation.bridge.LOGGER")
async def test_get_tender(mocked_logger):
    tender_data = TEST_TENDER
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



