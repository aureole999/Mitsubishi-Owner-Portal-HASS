"""The component."""
import datetime
import logging
import time
from asyncio import TimeoutError

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientConnectorError, ContentTypeError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import *
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from custom_components.mitsubishi_owner_portal.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(minutes=1)

CONF_ACCOUNTS = 'accounts'
CONF_API_BASE = 'api_base'
CONF_USER_ID = 'uid'
CONF_REFRESH_TOKEN = 'refresh_token'
CONF_TOKEN_TIME = 'token_time'
CONF_REFRESH_TOKEN_TIME = 'refresh_token_time'

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


async def async_setup(hass: HomeAssistant, hass_config: dict):
    # hass.data.setdefault(DOMAIN, {})
    # config = hass_config.get(DOMAIN) or {}
    # hass.data[DOMAIN]['config'] = config
    # hass.data[DOMAIN].setdefault(CONF_ACCOUNTS, {})
    # hass.data[DOMAIN].setdefault(CONF_DEVICES, {})
    # hass.data[DOMAIN].setdefault('coordinators', {})
    # hass.data[DOMAIN].setdefault('add_entities', {})
    #
    # component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    # hass.data[DOMAIN]['component'] = component
    # await component.async_setup(config)
    #
    # als = config.get(CONF_ACCOUNTS) or []
    # if CONF_PASSWORD in config:
    #     acc = {**config}
    #     acc.pop(CONF_ACCOUNTS, None)
    #     als.append(acc)
    # for cfg in als:
    #     if not cfg.get(CONF_PASSWORD) and not cfg.get(CONF_TOKEN):
    #         continue
    #     acc = MitsubishiOwnerPortalAccount(hass, cfg)
    #     coordinator = VehiclesCoordinator(acc)
    #     await coordinator.async_config_entry_first_refresh()
    #     hass.data[DOMAIN][CONF_ACCOUNTS][acc.uid] = acc
    #     hass.data[DOMAIN]['coordinators'][coordinator.name] = coordinator
    #
    # for platform in SUPPORTED_DOMAINS:
    #     hass.async_create_task(
    #         hass.helpers.discovery.async_load_platform(platform, DOMAIN, {}, config)
    #     )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config_data = hass.data.setdefault(DOMAIN, {})
    account = MitsubishiOwnerPortalAccount(hass, entry.data.get("account"))
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


class MitsubishiOwnerPortalAccount:
    def __init__(self, hass: HomeAssistant, config: dict):
        self._config = config
        self.hass = hass
        self.http = aiohttp_client.async_create_clientsession(hass, auto_cleanup=False)

    def get_config(self, key, default=None):
        return self._config.get(key, default)

    @property
    def username(self):
        return self.get_config(CONF_USERNAME)

    @property
    def password(self):
        pwd = self.get_config(CONF_PASSWORD)
        return pwd

    @property
    def uid(self):
        return self.get_config(CONF_USER_ID) or ''

    @property
    def token(self):
        return self.get_config(CONF_TOKEN) or ''

    @property
    def token_time(self):
        return self.get_config(CONF_TOKEN_TIME) or ''

    @property
    def refresh_token(self):
        return self.get_config(CONF_REFRESH_TOKEN) or ''

    @property
    def refresh_token_time(self):
        return self.get_config(CONF_REFRESH_TOKEN_TIME) or ''

    @property
    def update_interval(self):
        return self.get_config(CONF_SCAN_INTERVAL) or SCAN_INTERVAL

    def api_url(self, api=''):
        if api[:6] == 'https:' or api[:5] == 'http:':
            return api
        bas = self.get_config(CONF_API_BASE) or DEFAULT_API_BASE
        return f"{bas.rstrip('/')}/{api.lstrip('/')}"

    async def request(self, api, pms=None, method='GET', **kwargs):
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
        except (ClientConnectorError, ContentTypeError, TimeoutError) as exc:
            lgs = [method, url, pms, exc]
            if req:
                lgs.extend([req.status, req.content])
            _LOGGER.error('Request Mitsubishi owner portal api failed: %s', lgs)
        return {}

    async def async_login(self):
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
        self._config.update({
            CONF_TOKEN: access_token,
            CONF_TOKEN_TIME: time.time(),
            CONF_REFRESH_TOKEN: rsp.get('refresh_token'),
            CONF_REFRESH_TOKEN_TIME: time.time(),
            CONF_USER_ID: account_dn,
        })
        return True

    async def async_check_token(self):
        if None in [self.uid, self.token, self.token_time, self.refresh_token, self.refresh_token_time]:
            await self.async_login()
        elif time.time() - self.refresh_token_time > 2590000:
            await self.async_login()
        elif time.time() - self.token_time > 3000:
            await self.async_refresh_token()

    async def async_refresh_token(self):
        pms = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        rsp = await self.request(f'auth/v1/token', pms, 'POST')
        access_token = rsp.get('access_token')
        if not access_token:
            _LOGGER.warning('Mitsubishi owner portal refresh token failed: %s', rsp)
            return await self.async_login()
        self._config.update({
            CONF_TOKEN: access_token,
            CONF_TOKEN_TIME: time.time(),
            CONF_REFRESH_TOKEN: rsp.get('refresh_token'),
        })
        return True

    async def async_get_vehicles(self):
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
    def __init__(self, vin: str, account: MitsubishiOwnerPortalAccount):
        super().__init__(
            account.hass,
            _LOGGER,
            name=f'{DOMAIN}-{account.uid}-{CONF_DEVICES}',
            update_interval=account.update_interval,
        )
        self.account = account
        self.vin = vin
        self._subs = {}

    async def _async_update_data(self):
        return await self.update_vehicle_detail()

    async def update_vehicle_detail(self):
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

        ts = rsp.get('state', {}).get('chargingControl', {}).get('eventTimestamp', 'unknown')
        if ts.isnumeric():
            dt = datetime.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt = ts

        return {
            "Battery": rsp.get('state', {}).get('chargingControl', {}).get('hvBatteryLife', 'unknown'),
            "Charging_Status": rsp.get('state', {}).get('chargingControl', {}).get('hvChargingStatus', 'unknown'),
            "Charging_Mode": rsp.get('state', {}).get('chargingControl', {}).get('hvChargingMode', 'unknown'),
            "Charging_Plug_Status": rsp.get('state', {}).get('chargingControl', {}).get('hvChargingPlugStatus',
                                                                                        'unknown'),
            "Charging_Ready": rsp.get('state', {}).get('chargingControl', {}).get('hvChargingReady', 'unknown'),
            "Time_To_Full_Charge": rsp.get('state', {}).get('chargingControl', {}).get('hvTimeToFullCharge', 'unknown'),
            "Ignition_State": rsp.get('state', {}).get('ignitionState', 'unknown'),
            "Event_Timestamp": dt
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
    data: dict

    def __init__(self, dat: dict):
        self.data = dat

    @property
    def vin(self):
        return self.data.get('vin')

    @property
    def vehicle_model(self):
        return self.data.get('model', '')

    @property
    def vehicle_model_name(self):
        return self.data.get('modelDescription', '')


class MitsubishiOwnerPortalEntity(CoordinatorEntity[VehiclesCoordinator]):
    def __init__(self, vehicle, coordinator):
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
