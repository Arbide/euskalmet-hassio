"""Config flow for Euskalmet integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta, timezone

import aiohttp
import jwt
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    API_BASE_URL,
    API_STATIONS,
    API_GEO_REGIONS,
    API_GEO_ZONES,
    API_GEO_LOCATIONS,
    CONF_PRIVATE_KEY,
    CONF_FINGERPRINT,
    CONF_STATION,
    CONF_LOCATION,
    DOMAIN,
    JWT_ISSUER,
    JWT_AUDIENCE,
    JWT_VERSION,
    JWT_ALGORITHM,
)

_LOGGER = logging.getLogger(__name__)


def generate_jwt_token(private_key: str, fingerprint: str) -> str:
    """Generate JWT token for authentication."""
    now = datetime.now(timezone.utc)
    payload = {
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "version": JWT_VERSION,
        "iat": int(now.timestamp()),
        "loginId": fingerprint,
    }

    try:
        token = jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM)
        return token
    except Exception as err:
        _LOGGER.error("Error generating JWT token: %s", err)
        raise InvalidAuth


async def validate_credentials(
    hass: HomeAssistant, private_key: str, fingerprint: str
) -> bool:
    """Validate the credentials by trying to get stations."""
    try:
        token = generate_jwt_token(private_key, fingerprint)
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}{API_STATIONS}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 401:
                    return False
                response.raise_for_status()
                return True
    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        _LOGGER.error("Error validating credentials: %s", err)
        raise CannotConnect
    except Exception as err:
        _LOGGER.error("Unexpected error validating credentials: %s", err)
        raise CannotConnect


async def get_station_name(
    session: aiohttp.ClientSession, headers: dict, station_id: str
) -> str:
    """Get station name from API."""
    try:
        url = f"{API_BASE_URL}stations/{station_id}/current"
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                data = await response.json()
                if "name" in data:
                    # Prefer Spanish name, fallback to Basque
                    name = data["name"].get("SPANISH") or data["name"].get("BASQUE") or station_id
                    return name
    except Exception as err:
        _LOGGER.debug("Could not fetch name for station %s: %s", station_id, err)

    return station_id  # Fallback to ID if name not available


async def get_stations(hass: HomeAssistant, private_key: str, fingerprint: str) -> dict[str, str]:
    """Get list of stations from API."""
    try:
        token = generate_jwt_token(private_key, fingerprint)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        url = f"{API_BASE_URL}{API_STATIONS}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                data = await response.json()

                stations = {}
                seen_stations = set()
                station_list = []

                # API returns a list of station entries
                # Each station can have multiple entries (different snapshots)
                # We need to get unique station IDs
                if isinstance(data, list):
                    for entry in data:
                        station_id = entry.get("stationId")
                        if station_id and station_id not in seen_stations:
                            seen_stations.add(station_id)
                            station_list.append(station_id)

                _LOGGER.info("Found %d unique stations, fetching names...", len(station_list))

                # Fetch names for all stations
                station_names = {}
                for station_id in station_list:
                    station_name = await get_station_name(session, headers, station_id)
                    station_names[station_id] = station_name

                # Sort stations alphabetically by name
                sorted_stations = sorted(station_names.items(), key=lambda x: x[1].lower())

                # Create dictionary with format "Name (CODE)"
                for station_id, station_name in sorted_stations:
                    display_name = f"{station_name} ({station_id})"
                    stations[station_id] = display_name

                _LOGGER.info("Stations loaded and sorted: %d stations", len(stations))

                if not stations:
                    _LOGGER.warning("No stations found in API response")
                    raise CannotConnect

                return stations

    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        _LOGGER.error("Error fetching stations: %s", err)
        raise CannotConnect
    except Exception as err:
        _LOGGER.error("Unexpected error fetching stations: %s", err)
        raise CannotConnect


async def get_locations(
    hass: HomeAssistant, private_key: str, fingerprint: str
) -> dict[str, dict[str, str]]:
    """Fetch available locations from API.

    Returns:
        Dict of location_id: {
            "name": "Location Name",
            "region_id": "region_id",
            "zone_id": "zone_id",
            "display_name": "Location (Zone / Region)"
        }
    """
    try:
        token = generate_jwt_token(private_key, fingerprint)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        locations = {}

        async with aiohttp.ClientSession() as session:
            # Get regions
            regions_url = f"{API_BASE_URL}{API_GEO_REGIONS}"
            async with session.get(
                regions_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                regions_data = await response.json()

            # For each region, get zones
            for region in regions_data:
                region_id = region.get("regionId")
                if not region_id:
                    continue

                # Skip non-basque_country regions for now
                if region_id != "basque_country":
                    continue

                zones_url = f"{API_BASE_URL}{API_GEO_ZONES.format(region_id=region_id)}"
                async with session.get(
                    zones_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    zones_data = await response.json()

                # For each zone, get locations
                for zone in zones_data:
                    zone_id = zone.get("regionZoneId")
                    if not zone_id:
                        continue

                    locations_url = f"{API_BASE_URL}{API_GEO_LOCATIONS.format(region_id=region_id, zone_id=zone_id)}"
                    async with session.get(
                        locations_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        response.raise_for_status()
                        locations_data = await response.json()

                    # Process locations
                    for location in locations_data:
                        location_id = location.get("regionZoneLocationId")
                        if not location_id:
                            continue

                        # Format zone and region names for display
                        zone_name = zone_id.replace("_", " ").title()
                        region_name = region_id.replace("_", " ").title()
                        location_name = location_id.replace("_", " ").title()

                        # Special cases for known locations
                        location_name_map = {
                            "bilbao": "Bilbao",
                            "donostia": "Donostia-San Sebastián",
                            "vitoria-gasteiz": "Vitoria-Gasteiz",
                            "getxo": "Getxo",
                            "durango": "Durango",
                        }
                        location_name = location_name_map.get(
                            location_id, location_name
                        )

                        locations[location_id] = {
                            "name": location_name,
                            "region_id": region_id,
                            "zone_id": zone_id,
                            "display_name": f"{location_name} ({zone_name})",
                        }

            if not locations:
                _LOGGER.warning("No locations found in API response")
                raise CannotConnect

            return locations

    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        _LOGGER.error("Error fetching locations: %s", err)
        raise CannotConnect
    except Exception as err:
        _LOGGER.error("Unexpected error fetching locations: %s", err)
        raise CannotConnect


class EuskalmetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Euskalmet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.private_key: str | None = None
        self.fingerprint: str | None = None
        self.stations: dict[str, str] = {}
        self.locations: dict[str, dict[str, str]] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show menu for configuration type."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["station_config", "weather_config"],
        )

    async def async_step_station_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the station configuration step - credentials."""
        errors: dict[str, str] = {}

        # Check if there are existing entries to reuse credentials
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)

        if user_input is None and existing_entries:
            # Reuse credentials from first existing entry
            existing_entry = existing_entries[0]
            self.private_key = existing_entry.data[CONF_PRIVATE_KEY]
            self.fingerprint = existing_entry.data[CONF_FINGERPRINT]

            _LOGGER.info(
                "Reusing credentials from existing entry '%s' for new station configuration",
                existing_entry.title
            )

            try:
                # Fetch stations with existing credentials
                self.stations = await get_stations(
                    self.hass, self.private_key, self.fingerprint
                )

                # Move directly to station selection
                return await self.async_step_station()

            except (InvalidAuth, CannotConnect) as err:
                _LOGGER.warning(
                    "Could not reuse existing credentials: %s. Requesting new credentials.",
                    err
                )
                # Fall through to show credentials form

        if user_input is not None:
            try:
                # Validate credentials
                if await validate_credentials(
                    self.hass,
                    user_input[CONF_PRIVATE_KEY],
                    user_input[CONF_FINGERPRINT]
                ):
                    self.private_key = user_input[CONF_PRIVATE_KEY]
                    self.fingerprint = user_input[CONF_FINGERPRINT]

                    # Fetch stations
                    self.stations = await get_stations(
                        self.hass, self.private_key, self.fingerprint
                    )

                    # Move to station selection
                    return await self.async_step_station()
                else:
                    errors["base"] = "invalid_auth"

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Default values for form (use existing credentials if available)
        default_fingerprint = ""
        default_private_key = ""

        if existing_entries and not user_input:
            existing_entry = existing_entries[0]
            default_fingerprint = existing_entry.data.get(CONF_FINGERPRINT, "")
            default_private_key = existing_entry.data.get(CONF_PRIVATE_KEY, "")

        return self.async_show_form(
            step_id="station_config",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FINGERPRINT, default=default_fingerprint): str,
                    vol.Required(CONF_PRIVATE_KEY, default=default_private_key): TextSelector(
                        TextSelectorConfig(
                            multiline=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_weather_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the weather configuration step - credentials."""
        errors: dict[str, str] = {}

        # Check if there are existing entries to reuse credentials
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)

        if user_input is None and existing_entries:
            # Reuse credentials from first existing entry
            existing_entry = existing_entries[0]
            self.private_key = existing_entry.data[CONF_PRIVATE_KEY]
            self.fingerprint = existing_entry.data[CONF_FINGERPRINT]

            _LOGGER.info(
                "Reusing credentials from existing entry '%s' for weather configuration",
                existing_entry.title
            )

            try:
                # Fetch locations with existing credentials
                self.locations = await get_locations(
                    self.hass, self.private_key, self.fingerprint
                )

                # Move directly to location selection
                return await self.async_step_location()

            except (InvalidAuth, CannotConnect) as err:
                _LOGGER.warning(
                    "Could not reuse existing credentials: %s. Requesting new credentials.",
                    err
                )
                # Fall through to show credentials form

        if user_input is not None:
            try:
                # Validate credentials
                if await validate_credentials(
                    self.hass,
                    user_input[CONF_PRIVATE_KEY],
                    user_input[CONF_FINGERPRINT]
                ):
                    self.private_key = user_input[CONF_PRIVATE_KEY]
                    self.fingerprint = user_input[CONF_FINGERPRINT]

                    # Fetch locations
                    self.locations = await get_locations(
                        self.hass, self.private_key, self.fingerprint
                    )

                    # Move to location selection
                    return await self.async_step_location()
                else:
                    errors["base"] = "invalid_auth"

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Default values for form (use existing credentials if available)
        default_fingerprint = ""
        default_private_key = ""

        if existing_entries and not user_input:
            existing_entry = existing_entries[0]
            default_fingerprint = existing_entry.data.get(CONF_FINGERPRINT, "")
            default_private_key = existing_entry.data.get(CONF_PRIVATE_KEY, "")

        return self.async_show_form(
            step_id="weather_config",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FINGERPRINT, default=default_fingerprint): str,
                    vol.Required(CONF_PRIVATE_KEY, default=default_private_key): TextSelector(
                        TextSelectorConfig(
                            multiline=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the location selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            location_id = user_input[CONF_LOCATION]
            location_info = self.locations[location_id]

            # Create unique ID
            await self.async_set_unique_id(f"{DOMAIN}_weather_{location_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Euskalmet Weather - {location_info['name']}",
                data={
                    CONF_PRIVATE_KEY: self.private_key,
                    CONF_FINGERPRINT: self.fingerprint,
                    CONF_LOCATION: location_id,
                    "location_name": location_info["name"],
                    "region_id": location_info["region_id"],
                    "zone_id": location_info["zone_id"],
                },
            )

        # Create options for selector - sorted alphabetically
        sorted_locations = sorted(
            self.locations.items(),
            key=lambda x: x[1]["display_name"]
        )

        location_options = [
            {"label": info["display_name"], "value": location_id}
            for location_id, info in sorted_locations
        ]

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION): SelectSelector(
                        SelectSelectorConfig(
                            options=location_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the station selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION]

            # Fetch the actual station name now that a station has been selected
            try:
                token = generate_jwt_token(self.private_key, self.fingerprint)
                headers = {"Authorization": f"Bearer {token}"}

                async with aiohttp.ClientSession() as session:
                    station_name = await get_station_name(session, headers, station_id)
            except Exception as err:
                _LOGGER.warning("Could not fetch station name: %s", err)
                station_name = station_id

            # Create unique ID
            await self.async_set_unique_id(f"{DOMAIN}_{station_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Euskalmet - {station_name}",
                data={
                    CONF_PRIVATE_KEY: self.private_key,
                    CONF_FINGERPRINT: self.fingerprint,
                    CONF_STATION: station_id,
                },
            )

        # Create options for selector
        station_options = [
            {"label": name, "value": station_id}
            for station_id, name in self.stations.items()
        ]

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION): SelectSelector(
                        SelectSelectorConfig(
                            options=station_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
