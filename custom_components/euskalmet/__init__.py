"""The Euskalmet integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_PRIVATE_KEY, CONF_FINGERPRINT, CONF_STATION, CONF_LOCATION, DOMAIN
from .coordinator import EuskalmetDataUpdateCoordinator
from .weather_coordinator import EuskalmetWeatherUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Euskalmet from a config entry."""
    private_key = entry.data[CONF_PRIVATE_KEY]
    fingerprint = entry.data[CONF_FINGERPRINT]

    # Determine entry type and create appropriate coordinator
    if CONF_STATION in entry.data:
        # Station entry - create sensor coordinator
        station_id = entry.data[CONF_STATION]
        coordinator = EuskalmetDataUpdateCoordinator(
            hass, private_key, fingerprint, station_id
        )
        platforms = [Platform.SENSOR]

    elif CONF_LOCATION in entry.data:
        # Weather entry - create weather coordinator
        location_id = entry.data[CONF_LOCATION]
        region_id = entry.data.get("region_id", "basque_country")
        zone_id = entry.data.get("zone_id", "unknown")

        coordinator = EuskalmetWeatherUpdateCoordinator(
            hass, private_key, fingerprint, region_id, zone_id, location_id
        )
        platforms = [Platform.WEATHER]

    else:
        _LOGGER.error("Invalid config entry: missing station or location")
        return False

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up appropriate platforms
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Determine platforms to unload
    if CONF_STATION in entry.data:
        platforms = [Platform.SENSOR]
    elif CONF_LOCATION in entry.data:
        platforms = [Platform.WEATHER]
    else:
        return False

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, platforms):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok
