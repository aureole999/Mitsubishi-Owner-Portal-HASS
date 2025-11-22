"""Support for sensor."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    DOMAIN as ENTITY_DOMAIN, SensorEntityDescription, SensorDeviceClass, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime, UnitOfLength, UnitOfTemperature

from . import (
    DOMAIN,
    MitsubishiOwnerPortalEntity, VehiclesCoordinator, Vehicle,
)

_LOGGER = logging.getLogger(__name__)

DATA_KEY = f'{ENTITY_DOMAIN}.{DOMAIN}'

VEHICLE_SENSORS: tuple[SensorEntityDescription, ...] = (
    # Battery and Charging
    SensorEntityDescription(
        key="Battery",
        translation_key="current_battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Charging_Status",
        translation_key="charging_status",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="Charging_Plug_Status",
        translation_key="charging_plug_status",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="Charging_Mode",
        translation_key="charging_mode",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="Charging_Ready",
        translation_key="charging_ready",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="Time_To_Full_Charge",
        translation_key="time_to_full_charge",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        key="Event_Timestamp",
        translation_key="last_update_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),

    # Range Information
    SensorEntityDescription(
        key="Cruising_Range_Combined",
        translation_key="total_cruising_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:road-variant",
    ),
    SensorEntityDescription(
        key="Cruising_Range_Gasoline",
        translation_key="gasoline_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
    ),
    SensorEntityDescription(
        key="Cruising_Range_Electric",
        translation_key="electric_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ev-station",
    ),

    # Vehicle State
    SensorEntityDescription(
        key="Ignition_State",
        translation_key="ignition_state",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:key",
    ),
    SensorEntityDescription(
        key="Ignition_State_Timestamp",
        translation_key="ignition_state_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="Odometer",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    SensorEntityDescription(
        key="Odometer_Timestamp",
        translation_key="odometer_update_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),

    # Location Information
    SensorEntityDescription(
        key="Location_Latitude",
        translation_key="location_latitude",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="Location_Longitude",
        translation_key="location_longitude",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="Location_Timestamp",
        translation_key="location_update_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),

    # Security and Status
    SensorEntityDescription(
        key="Theft_Alarm",
        translation_key="theft_alarm",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:shield-car",
    ),
    SensorEntityDescription(
        key="Theft_Alarm_Type",
        translation_key="theft_alarm_type",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:shield-alert",
    ),
    SensorEntityDescription(
        key="Privacy_Mode",
        translation_key="privacy_mode",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:incognito",
    ),
    SensorEntityDescription(
        key="Temperature",
        translation_key="vehicle_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="Accessible",
        translation_key="vehicle_accessible",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:car-connected",
    ),

    # Other States
    SensorEntityDescription(
        key="Door_Status",
        translation_key="door_status",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:car-door",
    ),
    SensorEntityDescription(
        key="Diagnostic",
        translation_key="diagnostic_status",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:car-cog",
    ),
)


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    vhs = hass.data[DOMAIN][config_entry.entry_id].get("vhs", [])
    for v in vhs:
        async_add_entities(
            [MitsubishiOwnerPortalSensorEntity(v["vh"], v["coordinator"], desc) for desc in VEHICLE_SENSORS])


class MitsubishiOwnerPortalSensorEntity(MitsubishiOwnerPortalEntity, SensorEntity):
    """ MitsubishiOwnerPortalSensorEntity """
    entity_description: SensorEntityDescription

    def __init__(
            self,
            vehicle: Vehicle,
            coordinator: VehiclesCoordinator,
            description: SensorEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(vehicle, coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{vehicle.vin}_{self.entity_description.key}"
        )
        # Don't set _attr_name - let Home Assistant use translation_key
        self._attr_name = None

    @property
    def native_value(self):
        """Return the sensors state."""
        return self.coordinator.data[self.entity_description.key]
