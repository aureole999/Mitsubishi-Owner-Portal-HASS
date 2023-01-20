"""Support for sensor."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    DOMAIN as ENTITY_DOMAIN, SensorEntityDescription, SensorDeviceClass, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime

from . import (
    DOMAIN,
    MitsubishiOwnerPortalEntity, VehiclesCoordinator, Vehicle,
)

_LOGGER = logging.getLogger(__name__)

DATA_KEY = f'{ENTITY_DOMAIN}.{DOMAIN}'

VEHICLE_SENSORS: tuple[SensorEntityDescription, ...] = (
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
        key="Ignition_State",
        device_class=SensorDeviceClass.ENUM,
        name="Ignition State",
    ),
    SensorEntityDescription(
        key="Time_To_Full_Charge",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        name="Time To Full Charge",
    ),
    SensorEntityDescription(
        key="Event_Timestamp",
        name="Event Timestamp",
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
