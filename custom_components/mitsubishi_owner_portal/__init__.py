"""The component."""
import logging
import datetime
import time

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from homeassistant.core import HomeAssistant
from homeassistant.const import *
from homeassistant.components import persistent_notification
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import homeassistant.helpers.config_validation as cv

from asyncio import TimeoutError
from aiohttp import ClientConnectorError, ContentTypeError

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mitsubishi_owner_portal'
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
    hass.data.setdefault(DOMAIN, {})
    config = hass_config.get(DOMAIN) or {}
    hass.data[DOMAIN]['config'] = config
    hass.data[DOMAIN].setdefault(CONF_ACCOUNTS, {})
    hass.data[DOMAIN].setdefault(CONF_DEVICES, {})
    hass.data[DOMAIN].setdefault('coordinators', {})
    hass.data[DOMAIN].setdefault('add_entities', {})

    component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    hass.data[DOMAIN]['component'] = component
    await component.async_setup(config)

    als = config.get(CONF_ACCOUNTS) or []
    if CONF_PASSWORD in config:
        acc = {**config}
        acc.pop(CONF_ACCOUNTS, None)
        als.append(acc)
    for cfg in als:
        if not cfg.get(CONF_PASSWORD) and not cfg.get(CONF_TOKEN):
            continue
        acc = MitsubishiOwnerPortalAccount(hass, cfg)
        coordinator = VehiclesCoordinator(acc)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][CONF_ACCOUNTS][acc.uid] = acc
        hass.data[DOMAIN]['coordinators'][coordinator.name] = coordinator

    for platform in SUPPORTED_DOMAINS:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(platform, DOMAIN, {}, config)
        )

    return True


async def async_setup_accounts(hass: HomeAssistant, domain):
    for coordinator in hass.data[DOMAIN]['coordinators'].values():
        for k, sta in coordinator.data.items():
            await coordinator.update_hass_entities(domain, sta)


class MitsubishiOwnerPortalAccount:
    def __init__(self, hass: HomeAssistant, config: dict):
        self._config = config
        self.hass = hass
        self.http = aiohttp_client.async_create_clientsession(hass, auto_cleanup=False)

    def get_config(self, key, default=None):
        return self._config.get(key, self.hass.data[DOMAIN]['config'].get(key, default))

    @property
    def username(self):
        return self._config.get(CONF_USERNAME)

    @property
    def password(self):
        pwd = self._config.get(CONF_PASSWORD)
        return pwd

    @property
    def uid(self):
        return self._config.get(CONF_USER_ID) or ''

    @property
    def token(self):
        return self._config.get(CONF_TOKEN) or ''

    @property
    def token_time(self):
        return self._config.get(CONF_TOKEN_TIME) or ''

    @property
    def refresh_token(self):
        return self._config.get(CONF_REFRESH_TOKEN) or ''

    @property
    def refresh_token_time(self):
        return self._config.get(CONF_REFRESH_TOKEN_TIME) or ''

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

    async def async_refresh_token(self):
        if time.time() - self.refresh_token_time > 2590000:
            return await self.async_login()
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

    async def get_vehicles(self):
        uid = self._config.get(CONF_USER_ID)
        if uid is None:
            await self.async_login()
        if time.time() - self.token_time > 3000:
            await self.async_refresh_token()
        api = f'user/v1/users/{self._config.get(CONF_USER_ID)}/vehicles'
        rsp = await self.request(api)
        msg = rsp.get('message', '')
        if msg == 'Unauthorized':
            if await self.async_login():
                api = f'user/v1/users/{self._config.get(CONF_USER_ID)}/vehicles'
                rsp = await self.request(api)
        vhs = rsp.get('vehicles', {}) or []
        if not vhs:
            _LOGGER.warning('Got vehicles for %s failed: %s', self.username, rsp)
        return vhs


class VehiclesCoordinator(DataUpdateCoordinator):
    def __init__(self, account: MitsubishiOwnerPortalAccount):
        super().__init__(
            account.hass,
            _LOGGER,
            name=f'{DOMAIN}-{account.uid}-{CONF_DEVICES}',
            update_interval=account.update_interval,
        )
        self.account = account
        self._subs = {}

    async def _async_update_data(self):
        vhs = await self.account.get_vehicles()
        for vh in vhs:
            vin = vh.get('vin') or {}
            old = self.hass.data[DOMAIN][CONF_DEVICES].get(vin)
            if old:
                vehicle = old
                vehicle.update_data(vh)
            else:
                vehicle = Vehicle(vh, self)
                self.hass.data[DOMAIN][CONF_DEVICES][vin] = vehicle
            await vehicle.update_vehicle_detail()
            for d in SUPPORTED_DOMAINS:
                await self.update_hass_entities(d, vehicle)
        return self.hass.data[DOMAIN][CONF_DEVICES]

    async def update_hass_entities(self, domain, dvc):
        from .sensor import MitsubishiOwnerPortalSensorEntity
        hdk = f'hass_{domain}'
        add = self.hass.data[DOMAIN]['add_entities'].get(domain)
        if not add or not hasattr(dvc, hdk):
            return
        for k, cfg in getattr(dvc, hdk).items():
            key = f'{domain}.{k}.{dvc.vin}'
            new = None
            if key in self._subs:
                pass
            elif add and domain == 'sensor':
                new = MitsubishiOwnerPortalSensorEntity(k, dvc, cfg)
            if new:
                self._subs[key] = new
                add([new])


class Vehicle:
    data: dict

    def __init__(self, dat: dict, coordinator: VehiclesCoordinator):
        self.coordinator = coordinator
        self.account = coordinator.account
        self.listeners = {}
        self.update_data(dat)
        self.detail = {}

    def update_data(self, dat: dict):
        self.data = dat
        self._handle_listeners()
        _LOGGER.info('Update vehicle data: %s', dat)

    def _handle_listeners(self):
        for fun in self.listeners.values():
            fun()

    @property
    def vin(self):
        return self.data.get('vin')

    @property
    def vehicle_model(self):
        return self.data.get('model', '')

    @property
    def vehicle_model_name(self):
        return self.data.get('modelDescription', '')

    @property
    def hass_sensor(self):
        dat = {
            'battery': {
                'icon': 'mdi:battery',
                'unit': PERCENTAGE,
                'class': SensorDeviceClass.BATTERY,
                'state_class': SensorStateClass.MEASUREMENT,
            },
            'charging_status': {
                'icon': 'mdi:battery-charging',
            },
        }
        return dat

    @property
    def battery(self):
        return self.detail.get('state', {}).get('chargingControl', {}).get('hvBatteryLife', 'unknown')

    @property
    def charging_status(self):
        return self.detail.get('state', {}).get('chargingControl', {}).get('hvChargingStatus', 'unknown')

    async def update_vehicle_detail(self):
        # if not await self.async_remote_operation():
        #     return {}
        api = f'avi/v1/vehicles/{self.vin}/vehiclestate'
        try:
            rsp = await self.account.request(api)
        except (TypeError, ValueError) as exc:
            rsp = {}
            _LOGGER.error('Got vehicle detail for %s failed: %s', self.vehicle_model_name, exc)
        self.detail = rsp
        return rsp

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


class MitsubishiOwnerPortalEntity(CoordinatorEntity):
    def __init__(self, name, vehicle: Vehicle, option=None):
        self.coordinator = vehicle.coordinator
        CoordinatorEntity.__init__(self, self.coordinator)
        self.account = self.coordinator.account
        self._name = name
        self._device = vehicle
        self._option = option or {}
        self._attr_name = f'{vehicle.vehicle_model_name} {name}'.strip()
        self._attr_device_id = f'{vehicle.vehicle_model}_{vehicle.vin}'
        self._attr_unique_id = f'{self._attr_device_id}-{name}'
        self.entity_id = f'{DOMAIN}.{self._attr_device_id}_{name}'
        self._attr_icon = self._option.get('icon')
        self._attr_device_class = self._option.get('class')
        self._attr_state_class = self._option.get('state_class')
        self._attr_unit_of_measurement = self._option.get('unit')
        self._attr_device_info = {
            'identifiers': {(DOMAIN, self._attr_device_id)},
            'name': vehicle.data.get('name'),
            'model': vehicle.data.get('type'),
            'manufacturer': 'Petkit',
            'sw_version': vehicle.detail.get('firmware'),
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._device.listeners[self.entity_id] = self._handle_coordinator_update
        self._handle_coordinator_update()

    def _handle_coordinator_update(self):
        self.update()
        self.async_write_ha_state()

    def update(self):
        if hasattr(self._device, self._name):
            self._attr_state = getattr(self._device, self._name)
            _LOGGER.debug('Mitsubishi owner portal entity update: %s', [self.entity_id, self._name, self._attr_state])

        fun = self._option.get('state_attrs')
        if callable(fun):
            self._attr_extra_state_attributes = fun()

    @property
    def state(self):
        return self._attr_state

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    async def async_request_api(self, api, params=None, method='GET', **kwargs):
        throw = kwargs.pop('throw', None)
        rdt = await self.account.request(api, params, method, **kwargs)
        if throw:
            persistent_notification.create(
                self.hass,
                f'{rdt}',
                f'Request: {api}',
                f'{DOMAIN}-request',
            )
        return rdt
