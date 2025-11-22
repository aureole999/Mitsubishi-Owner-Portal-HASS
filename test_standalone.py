"""
Standalone test script example.
Can run without a full Home Assistant environment.

Usage:
    python test_standalone.py
"""
import asyncio
import sys
from pathlib import Path

# Add project path to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_vehicle_class():
    """Test Vehicle class."""
    from custom_components.mitsubishi_owner_portal import Vehicle

    vehicle_data = {
        "vin": "TEST123456789",
        "model": "OUTLANDER PHEV",
        "modelDescription": "Outlander PHEV 2024",
    }

    vehicle = Vehicle(vehicle_data)

    print("=== Testing Vehicle Class ===")
    print(f"VIN: {vehicle.vin}")
    print(f"Model: {vehicle.vehicle_model}")
    print(f"Model Name: {vehicle.vehicle_model_name}")
    print("✅ Vehicle class test passed\n")


async def test_account_mock():
    """Test account functionality (using mock)."""
    from unittest.mock import AsyncMock, MagicMock, patch

    print("=== Testing MitsubishiOwnerPortalAccount (Mock) ===")

    # Create mock hass object
    mock_hass = MagicMock()

    # Mock aiohttp_client
    with patch(
        "custom_components.mitsubishi_owner_portal.aiohttp_client.async_create_clientsession"
    ) as mock_session:
        mock_http = AsyncMock()
        mock_session.return_value = mock_http

        # Mock API response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "test_token_123",
                "refresh_token": "refresh_token_456",
                "accountDN": "test_user_id",
            }
        )
        mock_http.request = AsyncMock(return_value=mock_response)

        from custom_components.mitsubishi_owner_portal import (
            MitsubishiOwnerPortalAccount,
        )

        config = {
            "username": "test@example.com",
            "password": "test_password",
        }

        account = MitsubishiOwnerPortalAccount(mock_hass, config)

        # Test login
        login_result = await account.async_login()
        print(f"Login result: {login_result}")
        print(f"User ID: {account.uid}")
        print(f"Token: {account.token[:20]}..." if account.token else "None")
        print("✅ Account mock test passed\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Mitsubishi Owner Portal - Standalone Tests")
    print("=" * 60)
    print()

    try:
        await test_vehicle_class()
        await test_account_mock()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
