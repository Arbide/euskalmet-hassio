"""Support for Euskalmet weather sensors."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_STATION,
    DOMAIN,
    SENSOR_TYPES,
)
from .coordinator import EuskalmetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Euskalmet sensor entities."""
    coordinator: EuskalmetDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION]

    # Wait for first update to detect available sensors
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Create sensor entities only for available sensor types
    for sensor_type in coordinator.available_sensor_types:
        if sensor_type in SENSOR_TYPES:
            sensor_info = SENSOR_TYPES[sensor_type]
            entities.append(
                EuskalmetSensor(
                    coordinator,
                    station_id,
                    sensor_type,
                    sensor_info,
                )
            )

    _LOGGER.info(
        "Created %d sensor entities for station %s: %s",
        len(entities),
        station_id,
        list(coordinator.available_sensor_types),
    )

    async_add_entities(entities)


class EuskalmetSensor(CoordinatorEntity[EuskalmetDataUpdateCoordinator], SensorEntity):
    """Representation of an Euskalmet sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EuskalmetDataUpdateCoordinator,
        station_id: str,
        sensor_type: str,
        sensor_info: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._station_id = station_id
        self._sensor_type = sensor_type
        self._attr_name = sensor_info["name"]
        self._attr_native_unit_of_measurement = sensor_info.get("unit")
        self._attr_device_class = sensor_info.get("device_class")
        self._attr_state_class = sensor_info.get("state_class")
        self._attr_icon = sensor_info.get("icon")
        self._attr_suggested_display_precision = sensor_info.get("suggested_display_precision")

        # Unique ID
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{sensor_type}"

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, station_id)},
            "name": f"Euskalmet {station_id}",
            "manufacturer": "Euskalmet",
            "model": "Weather Station",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(self._sensor_type)

        if value is None:
            return None

        # Convert value to appropriate type
        try:
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                # Try to convert to float
                try:
                    return float(value)
                except ValueError:
                    return value
        except Exception as err:
            _LOGGER.error("Error converting sensor value: %s", err)
            return None

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}

        if self.coordinator.data:
            # Add last update time
            last_update = self.coordinator.data.get("last_update")
            if last_update:
                attributes["last_update"] = last_update

            # Add station info
            attributes["station_id"] = self._station_id

            # Add station name if available
            if self.coordinator.station_name:
                attributes["station_name"] = self.coordinator.station_name

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get(self._sensor_type) is not None
        )
