"""Fixtures for Mitsubishi Owner Portal integration tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_setup_entry() -> None:
    """Override async_setup_entry."""
    with patch(
        "custom_components.mitsubishi_owner_portal.async_setup_entry",
        return_value=True,
    ):
        yield


@pytest.fixture
def mock_mitsubishi_account():
    """Mock Mitsubishi Owner Portal account."""
    with patch(
        "custom_components.mitsubishi_owner_portal.MitsubishiOwnerPortalAccount"
    ) as mock_account:
        account = mock_account.return_value
        account.async_login = AsyncMock(return_value=True)
        account.async_get_vehicles = AsyncMock(
            return_value=[
                {
                    "vin": "TEST123456789",
                    "model": "OUTLANDER PHEV",
                    "modelDescription": "Outlander PHEV 2024",
                }
            ]
        )
        account.uid = "test_user_id"
        yield account
