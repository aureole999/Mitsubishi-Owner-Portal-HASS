"""Test the Mitsubishi Owner Portal config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.mitsubishi_owner_portal.const import DOMAIN


@pytest.fixture
def mock_account():
    """Mock account."""
    with patch(
        "custom_components.mitsubishi_owner_portal.config_flow.MitsubishiOwnerPortalAccount"
    ) as mock:
        account = mock.return_value
        account.async_login = AsyncMock(return_value=True)
        account.async_get_vehicles = AsyncMock(
            return_value=[
                {
                    "vin": "TEST123",
                    "model": "Test Model",
                    "modelDescription": "Test Vehicle",
                }
            ]
        )
        account.uid = "test_uid"
        yield mock


async def test_form_user(hass: HomeAssistant, mock_account) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "test_password",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "test@example.com"
    assert result2["data"]["account"]["username"] == "test@example.com"


async def test_form_invalid_auth(hass: HomeAssistant, mock_account) -> None:
    """Test we handle invalid auth."""
    mock_account.return_value.async_login = AsyncMock(return_value=False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "wrong_password",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "auth_error"}
