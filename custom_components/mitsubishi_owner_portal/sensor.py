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
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        name="Current Battery Level",
    ),
    SensorEntityDescription(
        key="Charging_Status",
        device_class=SensorDeviceClass.ENUM,
        name="Charging Status",
    ),
    SensorEntityDescription(
        key="Charging_Plug_Status",
        device_class=SensorDeviceClass.ENUM,
        name="Charging Plug Status",
    ),
    SensorEntityDescription(
        key="Charging_Mode",
        device_class=SensorDeviceClass.ENUM,
        name="Charging Mode",
    ),
    SensorEntityDescription(
        key="Charging_Ready",
        device_class=SensorDeviceClass.ENUM,
        name="Charging Ready",
    ),
    SensorEntityDescription(
        key="Time_To_Full_Charge",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        name="Time To Full Charge",
    ),
    SensorEntityDescription(
        key="Event_Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="Last Update Time",
    ),

    # Range Information
    SensorEntityDescription(
        key="Cruising_Range_Combined",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        name="Total Cruising Range",
        icon="mdi:road-variant",
    ),
    SensorEntityDescription(
        key="Cruising_Range_Gasoline",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        name="Gasoline Range",
        icon="mdi:gas-station",
    ),
    SensorEntityDescription(
        key="Cruising_Range_Electric",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        name="Electric Range",
        icon="mdi:ev-station",
    ),

    # Vehicle State
    SensorEntityDescription(
        key="Ignition_State",
        device_class=SensorDeviceClass.ENUM,
        name="Ignition State",
        icon="mdi:key",
    ),
    SensorEntityDescription(
        key="Ignition_State_Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="Ignition State Time",
    ),
    SensorEntityDescription(
        key="Odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Odometer",
        icon="mdi:counter",
    ),
    SensorEntityDescription(
        key="Odometer_Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="Odometer Update Time",
    ),

    # Location Information
    SensorEntityDescription(
        key="Location_Latitude",
        name="Location Latitude",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="Location_Longitude",
        name="Location Longitude",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="Location_Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        name="Location Update Time",
    ),

    # Security and Status
    SensorEntityDescription(
        key="Theft_Alarm",
        device_class=SensorDeviceClass.ENUM,
        name="Theft Alarm",
        icon="mdi:shield-car",
    ),
    SensorEntityDescription(
        key="Theft_Alarm_Type",
        device_class=SensorDeviceClass.ENUM,
        name="Theft Alarm Type",
        icon="mdi:shield-alert",
    ),
    SensorEntityDescription(
        key="Privacy_Mode",
        device_class=SensorDeviceClass.ENUM,
        name="Privacy Mode",
        icon="mdi:incognito",
    ),
    SensorEntityDescription(
        key="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        name="Vehicle Temperature",
    ),
    SensorEntityDescription(
        key="Accessible",
        device_class=SensorDeviceClass.ENUM,
        name="Vehicle Accessible",
        icon="mdi:car-connected",
    ),

    # Other States
    SensorEntityDescription(
        key="Door_Status",
        device_class=SensorDeviceClass.ENUM,
        name="Door Status",
        icon="mdi:car-door",
    ),
    SensorEntityDescription(
        key="Diagnostic",
        device_class=SensorDeviceClass.ENUM,
        name="Diagnostic Status",
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

    @property
    def name(self) -> str:
        """Return the name of the Smart Plug.

        Overridden to include the description.
        """
        return f"{self.vehicle.vehicle_model} {self.entity_description.name}"

    @property
    def native_value(self):
        """Return the sensors state."""
        return self.coordinator.data[self.entity_description.key]
