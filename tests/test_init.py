"""Test Mitsubishi Owner Portal setup process."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.mitsubishi_owner_portal.const import DOMAIN


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test Vehicle",
        data={
            "account": {
                "username": "test@example.com",
                "password": "test_password",
                "uid": "test_uid",
            },
            "vehicles": [
                {
                    "vin": "TEST123",
                    "model": "Test Model",
                    "modelDescription": "Test Vehicle",
                }
            ],
        },
        source="user",
    )


async def test_setup_entry(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test setup of a config entry."""
    with patch(
        "custom_components.mitsubishi_owner_portal.MitsubishiOwnerPortalAccount"
    ) as mock_account_class:
        mock_account = mock_account_class.return_value
        mock_account.async_get_vehicles = AsyncMock(
            return_value=[
                {
                    "vin": "TEST123",
                    "model": "Test Model",
                    "modelDescription": "Test Vehicle",
                }
            ]
        )

        with patch(
            "custom_components.mitsubishi_owner_portal.VehiclesCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ):
            assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
            await hass.async_block_till_done()

    assert mock_config_entry.entry_id in hass.data[DOMAIN]
