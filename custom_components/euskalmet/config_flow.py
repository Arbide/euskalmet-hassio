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
    TextSelectorType,
)

from .const import (
    API_BASE_URL,
    API_STATIONS,
    CONF_PRIVATE_KEY,
    CONF_FINGERPRINT,
    CONF_STATION,
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


async def get_stations(hass: HomeAssistant, private_key: str, fingerprint: str) -> dict[str, str]:
    """Get list of stations from API."""
    try:
        token = generate_jwt_token(private_key, fingerprint)
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}{API_STATIONS}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

                stations = {}
                # Parse stations from response
                # The actual structure depends on the API response
                # This is a simplified version that may need adjustment
                if isinstance(data, dict) and "stations" in data:
                    for station in data["stations"]:
                        station_id = str(station.get("id", station.get("stationCode", "")))
                        station_name = station.get("name", station.get("stationName", f"Station {station_id}"))
                        if station_id:
                            stations[station_id] = station_name
                elif isinstance(data, list):
                    for station in data:
                        station_id = str(station.get("id", station.get("stationCode", "")))
                        station_name = station.get("name", station.get("stationName", f"Station {station_id}"))
                        if station_id:
                            stations[station_id] = station_name

                if not stations:
                    _LOGGER.warning("No stations found in API response")
                    # Fallback - return a test station for development
                    stations = {"test": "Test Station"}

                return stations

    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        _LOGGER.error("Error fetching stations: %s", err)
        raise CannotConnect
    except Exception as err:
        _LOGGER.error("Unexpected error fetching stations: %s", err)
        raise CannotConnect


class EuskalmetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Euskalmet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.private_key: str | None = None
        self.fingerprint: str | None = None
        self.stations: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - credentials."""
        errors: dict[str, str] = {}

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

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FINGERPRINT): str,
                    vol.Required(CONF_PRIVATE_KEY): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                            multiline=True,
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
            station_name = self.stations.get(station_id, "Unknown Station")

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
