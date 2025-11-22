"""The Mitsubishi Owner Portal integration."""
from __future__ import annotations

import datetime
import logging
import time
from asyncio import TimeoutError
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientConnectorError, ClientSSLError, ContentTypeError
from homeassistant.components.persistent_notification import async_create
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, issue_registry as ir
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(minutes=1)

CONF_ACCOUNTS = 'accounts'
CONF_API_BASE = 'api_base'
CONF_USER_ID = 'uid'
CONF_REFRESH_TOKEN = 'refresh_token'
CONF_TOKEN_TIME = 'token_time'
CONF_REFRESH_TOKEN_TIME = 'refresh_token_time'
CONF_VERIFY_SSL = 'verify_ssl'

DEFAULT_API_BASE = 'https://connect.mitsubishi-motors.co.jp/'

SUPPORTED_DOMAINS = [
    'sensor',
]

ACCOUNT_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_API_BASE, default=DEFAULT_API_BASE): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: ACCOUNT_SCHEMA.extend(
            {
                vol.Optional(CONF_ACCOUNTS): vol.All(cv.ensure_list, [ACCOUNT_SCHEMA]),
            },
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, hass_config: dict[str, Any]) -> bool:
    """Set up the Mitsubishi Owner Portal component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mitsubishi Owner Portal from a config entry."""
    config_data = hass.data.setdefault(DOMAIN, {})
    account = MitsubishiOwnerPortalAccount(hass, entry.data.get("account"), entry=entry)
    vehicles_data = await account.async_get_vehicles()
    vhs = []
    for vehicle in vehicles_data:
        vh = Vehicle(vehicle)
        coordinator = VehiclesCoordinator(vh.vin, account)
        await coordinator.async_config_entry_first_refresh()
        vhs.append({"vh": vh, "coordinator": coordinator})
    config_data.update({entry.entry_id: {"account": account, "vhs": vhs}})
    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_DOMAINS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, SUPPORTED_DOMAINS)

    if unload_ok:
        # Clean up stored data
        config_data = hass.data.get(DOMAIN, {})
        if entry.entry_id in config_data:
            entry_data = config_data.pop(entry.entry_id)
            # Close HTTP session if it exists
            if "account" in entry_data and hasattr(entry_data["account"], "http"):
                await entry_data["account"].http.close()
            _LOGGER.info("Successfully unloaded Mitsubishi Owner Portal entry: %s", entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class MitsubishiOwnerPortalAccount:
    """Mitsubishi Owner Portal account handler."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the account."""
        self._config = config
        self.hass = hass
        self.entry = entry

        # Determine if SSL verification should be enabled
        verify_ssl = self.get_config(CONF_VERIFY_SSL, True)

        if not verify_ssl:
            _LOGGER.warning(
                "SSL verification is disabled. This is insecure and should only be used for testing."
            )

        self.http = aiohttp_client.async_create_clientsession(
            hass,
            verify_ssl=verify_ssl,
            auto_cleanup=False,
        )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    @property
    def username(self) -> str | None:
        """Get username."""
        return self.get_config(CONF_USERNAME)

    @property
    def password(self) -> str | None:
        """Get password."""
        return self.get_config(CONF_PASSWORD)

    @property
    def uid(self) -> str:
        """Get user ID."""
        return self.get_config(CONF_USER_ID) or ''

    @property
    def token(self) -> str:
        """Get access token."""
        return self.get_config(CONF_TOKEN) or ''

    @property
    def token_time(self) -> float:
        """Get token timestamp."""
        return self.get_config(CONF_TOKEN_TIME) or 0

    @property
    def refresh_token(self) -> str:
        """Get refresh token."""
        return self.get_config(CONF_REFRESH_TOKEN) or ''

    @property
    def refresh_token_time(self) -> float:
        """Get refresh token timestamp."""
        return self.get_config(CONF_REFRESH_TOKEN_TIME) or 0

    @property
    def update_interval(self) -> datetime.timedelta:
        """Get update interval."""
        return self.get_config(CONF_SCAN_INTERVAL) or SCAN_INTERVAL

    def api_url(self, api: str = '') -> str:
        """Build API URL."""
        if api[:6] == 'https:' or api[:5] == 'http:':
            return api
        bas = self.get_config(CONF_API_BASE) or DEFAULT_API_BASE
        return f"{bas.rstrip('/')}/{api.lstrip('/')}"

    async def request(
        self, api: str, pms: dict[str, Any] | None = None, method: str = 'GET', **kwargs: Any
    ) -> dict[str, Any]:
        """Make API request."""
        method = method.upper()
        url = self.api_url(api)
        kws = {
            'timeout': 30,
            'headers': {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*'
            },
        }
        kws.update(kwargs)
        if method in ['GET']:
            kws['params'] = pms
        elif method in ['POST_GET']:
            method = 'POST'
            kws['params'] = pms
        else:
            kws['json'] = pms
        req = None
        try:
            req = await self.http.request(method, url, **kws)
            return await req.json(content_type=None) or {}
        except ClientSSLError as exc:
            # SSL Certificate error - create repair issue
            _LOGGER.error('SSL certificate error connecting to %s: %s', url, exc)
            self._create_ssl_error_issue(url, str(exc))
            raise UpdateFailed(f"SSL certificate error: {exc}") from exc
        except ClientConnectorError as exc:
            # Mask sensitive data in logs
            safe_pms = {**pms} if pms else {}
            if 'password' in safe_pms:
                safe_pms['password'] = '***'
            if 'refresh_token' in safe_pms:
                safe_pms['refresh_token'] = safe_pms['refresh_token'][:10] + '...'

            _LOGGER.error(
                'Connection error to Mitsubishi API: method=%s, url=%s, error=%s',
                method,
                url,
                type(exc).__name__,
            )
            _LOGGER.debug('Request params (safe): %s', safe_pms)

            # Check if it's a certificate error
            if 'CERTIFICATE' in str(exc).upper() or 'SSL' in str(exc).upper():
                self._create_ssl_error_issue(url, str(exc))

            if req:
                _LOGGER.debug('Response status: %s', req.status)

        except (ContentTypeError, TimeoutError) as exc:
            _LOGGER.error(
                'Request to Mitsubishi API failed: method=%s, url=%s, error=%s',
                method,
                url,
                type(exc).__name__,
            )

        return {}

    def _create_ssl_error_issue(self, url: str, error: str) -> None:
        """Create a repair issue for SSL certificate errors."""
        if not self.entry:
            return

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"ssl_certificate_error_{self.entry.entry_id}",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="ssl_certificate_error",
            translation_placeholders={
                "url": url,
                "error": error,
            },
        )

        # Also create a persistent notification for immediate visibility
        async_create(
            self.hass,
            f"SSL certificate error when connecting to Mitsubishi Owner Portal.\n\n"
            f"URL: {url}\n"
            f"Error: {error}\n\n"
            f"This usually means:\n"
            f"1. The server's SSL certificate has expired\n"
            f"2. Your system's CA certificates need updating\n"
            f"3. There's a network issue\n\n"
            f"Please check the [repair issues](/config/repairs) for more details.",
            title="Mitsubishi Owner Portal SSL Error",
            notification_id=f"mitsubishi_ssl_error_{self.entry.entry_id}",
        )

    async def async_login(self) -> bool:
        """Log in to Mitsubishi Owner Portal."""
        pms = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password,
        }
        rsp = await self.request(f'auth/v1/token', pms, 'POST')
        account_dn = rsp.get('accountDN')
        access_token = rsp.get('access_token')
        if not account_dn:
            _LOGGER.error('Mitsubishi owner portal login %s failed: %s', self.username, rsp)
            return False

        # Update in-memory config
        current_time = time.time()
        self._config.update({
            CONF_TOKEN: access_token,
            CONF_TOKEN_TIME: current_time,
            CONF_REFRESH_TOKEN: rsp.get('refresh_token'),
            CONF_REFRESH_TOKEN_TIME: current_time,
            CONF_USER_ID: account_dn,
        })

        # Persist to config entry
        if self.entry:
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    "account": self._config.copy(),
                },
            )
            _LOGGER.info("Login successful, credentials saved to config entry")
        else:
            _LOGGER.info("Login successful (no config entry to save)")

        return True

    async def async_check_token(self) -> None:
        """Check and refresh token if needed."""
        current_time = time.time()
        token_age = current_time - self.token_time if self.token_time else 0
        refresh_token_age = current_time - self.refresh_token_time if self.refresh_token_time else 0

        _LOGGER.debug(
            "Token check: token_age=%ds, refresh_age=%ds, uid=%s",
            int(token_age),
            int(refresh_token_age),
            self.uid or "None",
        )

        if None in [self.uid, self.token, self.token_time, self.refresh_token, self.refresh_token_time]:
            _LOGGER.info("Missing credentials, performing login")
            await self.async_login()
        elif refresh_token_age > 2590000:  # ~30 days
            _LOGGER.info("Refresh token expired (age: %d days), performing re-login", int(refresh_token_age / 86400))
            await self.async_login()
        elif token_age > 1500:  # 25 minutes
            _LOGGER.debug("Access token expired (age: %d minutes), refreshing", int(token_age / 60))
            await self.async_refresh_token()

    async def async_refresh_token(self) -> bool:
        """Refresh access token."""
        pms = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        rsp = await self.request(f'auth/v1/token', pms, 'POST')
        access_token = rsp.get('access_token')
        if not access_token:
            _LOGGER.warning('Mitsubishi owner portal refresh token failed: %s', rsp)
            return await self.async_login()

        # Update in-memory config
        self._config.update({
            CONF_TOKEN: access_token,
            CONF_TOKEN_TIME: time.time(),
            CONF_REFRESH_TOKEN: rsp.get('refresh_token'),
        })

        # Persist to config entry
        if self.entry:
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    "account": self._config.copy(),
                },
            )
            _LOGGER.debug("Access token refreshed and saved to config entry")

        return True

    async def async_get_vehicles(self) -> list[dict[str, Any]]:
        """Get list of vehicles."""
        await self.async_check_token()
        api = f'user/v1/users/{self.uid}/vehicles'
        rsp = await self.request(api)
        msg = rsp.get('message', '')
        if msg == 'Unauthorized':
            if await self.async_login():
                api = f'user/v1/users/{self.uid}/vehicles'
                rsp = await self.request(api)
        vhs = rsp.get('vehicles', [])
        if not vhs:
            _LOGGER.warning('Got vehicles for %s failed: %s', self.username, rsp)
        return vhs


class VehiclesCoordinator(DataUpdateCoordinator):
    """Vehicle data update coordinator."""

    def __init__(self, vin: str, account: MitsubishiOwnerPortalAccount) -> None:
        """Initialize the coordinator."""
        super().__init__(
            account.hass,
            _LOGGER,
            name=f'{DOMAIN}-{account.uid}-{vin}',
            update_interval=account.update_interval,
        )
        self.account = account
        self.vin = vin
        self._subs = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        return await self.update_vehicle_detail()

    async def update_vehicle_detail(self) -> dict[str, Any]:
        """Update vehicle detail."""
        # if not await self.async_remote_operation():
        #     return {}
        await self.account.async_check_token()
        api = f'avi/v1/vehicles/{self.vin}/vehiclestate'
        try:
            rsp = await self.account.request(api)
        except (TypeError, ValueError) as exc:
            rsp = {}
            _LOGGER.error('Got vehicle detail for %s failed: %s', self.vin, exc)

        if not rsp.get('state', {}):
            _LOGGER.warning('Got vehicle detail for %s failed: %s', self.vin, rsp)
            if await self.account.async_login():
                try:
                    rsp = await self.account.request(api)
                except (TypeError, ValueError):
                    rsp = {}

        state = rsp.get('state', {})
        charging_control = state.get('chargingControl', {})

        # Helper function to convert timestamp
        def format_timestamp(ts_value):
            if ts_value and str(ts_value).isnumeric():
                timestamp = float(ts_value)
                # Check if timestamp is in milliseconds (13 digits) and convert to seconds
                if timestamp > 10000000000:  # Timestamps after year 2286 are likely in milliseconds
                    timestamp = timestamp / 1000
                return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            return ts_value or 'unknown'

        # Extract location data
        ext_loc_map = state.get('extLocMap', {})
        location_lat = ext_loc_map.get('lat', 'unknown')
        location_lon = ext_loc_map.get('lon', 'unknown')
        location_ts = format_timestamp(ext_loc_map.get('ts'))

        # Extract odometer data (get the most recent reading)
        odo_list = state.get('odo', [])
        latest_odo = 'unknown'
        latest_odo_ts = 'unknown'
        if odo_list and isinstance(odo_list, list):
            latest_odo_entry = odo_list[-1] if odo_list else {}
            if isinstance(latest_odo_entry, dict) and latest_odo_entry:
                # Get the first (and only) key-value pair
                for ts_key, odo_value in latest_odo_entry.items():
                    latest_odo = odo_value
                    latest_odo_ts = ts_key
                    break

        # Extract cruising range data
        cruising_range_combined = charging_control.get('cruisingRangeCombined', 'unknown')

        # Extract first cruising range (gasoline)
        cruising_range_first_list = charging_control.get('cruisingRangeFirst', [])
        cruising_range_gasoline = 'unknown'
        if cruising_range_first_list and isinstance(cruising_range_first_list, list):
            for item in cruising_range_first_list:
                if isinstance(item, dict) and item.get('engineType') == '4':
                    cruising_range_gasoline = item.get('range', 'unknown')
                    break

        # Extract second cruising range (electric)
        cruising_range_second_list = charging_control.get('cruisingRangeSecond', [])
        cruising_range_electric = 'unknown'
        if cruising_range_second_list and isinstance(cruising_range_second_list, list):
            for item in cruising_range_second_list:
                if isinstance(item, dict) and item.get('engineType') == '5':
                    cruising_range_electric = item.get('range', 'unknown')
                    break

        return {
            # Charging information
            "Battery": charging_control.get('hvBatteryLife', 'unknown'),
            "Charging_Status": charging_control.get('hvChargingStatus', 'unknown'),
            "Charging_Mode": charging_control.get('hvChargingMode', 'unknown'),
            "Charging_Plug_Status": charging_control.get('hvChargingPlugStatus', 'unknown'),
            "Charging_Ready": charging_control.get('hvChargingReady', 'unknown'),
            "Time_To_Full_Charge": charging_control.get('hvTimeToFullCharge', 'unknown'),
            "Event_Timestamp": format_timestamp(charging_control.get('eventTimestamp')),

            # Range information
            "Cruising_Range_Combined": cruising_range_combined,
            "Cruising_Range_Gasoline": cruising_range_gasoline,
            "Cruising_Range_Electric": cruising_range_electric,

            # Vehicle state
            "Ignition_State": state.get('ignitionState', 'unknown'),
            "Ignition_State_Timestamp": format_timestamp(state.get('ignitionStateTs')),
            "Odometer": latest_odo,
            "Odometer_Timestamp": latest_odo_ts,

            # Location information
            "Location_Latitude": location_lat,
            "Location_Longitude": location_lon,
            "Location_Timestamp": location_ts,

            # Security and status
            "Theft_Alarm": state.get('theftAlarm', 'unknown'),
            "Theft_Alarm_Type": state.get('theftAlarmType', 'unknown'),
            "Privacy_Mode": state.get('privacy', 'unknown'),
            "Temperature": state.get('temp', 'unknown'),
            "Accessible": state.get('accessible', 'unknown'),

            # Other states
            "Door_Status": state.get('ods', 'unknown'),
            "Diagnostic": state.get('diagnostic', 'unknown'),
        }

    async def async_remote_operation(self):
        pms = {
            'forced': 'true',
            'operation': 'vehicleStatus',
            'userAgent': 'owner-portal',
            'vin': self.vin
        }
        attempts = 0
        eid = None
        while attempts < 3:
            attempts += 1
            rsp = await self.account.request(f'avi/v3/remoteOperation', pms, 'POST')
            msg = rsp.get('message', '')
            if msg == 'Unauthorized':
                await self.account.async_login()
                rsp = await self.account.request(f'avi/v3/remoteOperation', pms, 'POST')

            eid = rsp.get('eventId')
            status = rsp.get('status')
            if status == 'Started':
                break
            time.sleep(5)

        if not eid:
            _LOGGER.error('Request remote api failed')
            return False

        time.sleep(3)
        attempts = 0
        while attempts < 5:
            attempts += 1
            rsp = await self.account.request(f'avi/v1/remoteOperation/vehicles/{self.vin}/events/{eid}')
            status = rsp.get('status')
            if status == 'Successful':
                return True
            time.sleep(5)
        _LOGGER.error('Get remote api response failed')
        return False


class Vehicle:
    """Vehicle data model."""

    def __init__(self, dat: dict[str, Any]) -> None:
        """Initialize vehicle."""
        self.data: dict[str, Any] = dat

    @property
    def vin(self) -> str | None:
        """Get VIN."""
        return self.data.get('vin')

    @property
    def vehicle_model(self) -> str:
        """Get vehicle model."""
        return self.data.get('model', '')

    @property
    def vehicle_model_name(self) -> str:
        """Get vehicle model name."""
        return self.data.get('modelDescription', '')


class MitsubishiOwnerPortalEntity(CoordinatorEntity[VehiclesCoordinator]):
    """Base entity for Mitsubishi Owner Portal."""

    def __init__(self, vehicle: Vehicle, coordinator: VehiclesCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.vehicle = vehicle
        self._attr_name = vehicle.vehicle_model_name
        self._attr_unique_id = vehicle.vin

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.vehicle.vin))},
            manufacturer="Mitsubishi",
            model=self.vehicle.vehicle_model,
            name=self.vehicle.vehicle_model_name,
        )
