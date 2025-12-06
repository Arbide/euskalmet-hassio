"""Data update coordinator for Euskalmet integration."""
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp
import jwt

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import (
    API_BASE_URL,
    DOMAIN,
    UPDATE_INTERVAL,
    JWT_ISSUER,
    JWT_AUDIENCE,
    JWT_VERSION,
    JWT_ALGORITHM,
)

_LOGGER = logging.getLogger(__name__)

# Mapping of sensor types to measurement IDs and sensor types
# This will need to be expanded as we identify more sensor types
SENSOR_MAPPINGS = {
    "temperature": {"measureType": "measuresForAmbient", "measure": "temp"},
    "humidity": {"measureType": "measuresForAmbient", "measure": "hum"},
    "wind_speed": {"measureType": "measuresForWind", "measure": "mean_speed"},
    "wind_direction": {"measureType": "measuresForWind", "measure": "mean_direction"},
    "pressure": {"measureType": "measuresForPressure", "measure": "pressure"},
    "precipitation": {"measureType": "measuresForRain", "measure": "rain_acc"},
}


class EuskalmetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Euskalmet data."""

    def __init__(
        self,
        hass: HomeAssistant,
        private_key: str,
        fingerprint: str,
        station_id: str,
    ) -> None:
        """Initialize the coordinator."""
        self.private_key = private_key
        self.fingerprint = fingerprint
        self.station_id = station_id
        self.station_name = ""
        self._session = aiohttp.ClientSession()
        self._station_sensors = {}  # Cache of sensor information

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    def _generate_jwt_token(self) -> str:
        """Generate JWT token for authentication."""
        now = datetime.now(timezone.utc)
        payload = {
            "aud": JWT_AUDIENCE,
            "iss": JWT_ISSUER,
            "exp": int((now + timedelta(days=365)).timestamp()),
            "version": JWT_VERSION,
            "iat": int(now.timestamp()),
            "loginId": self.fingerprint,
        }

        try:
            token = jwt.encode(payload, self.private_key, algorithm=JWT_ALGORITHM)
            return token
        except Exception as err:
            _LOGGER.error("Error generating JWT token: %s", err)
            raise ConfigEntryAuthFailed("Invalid private key") from err

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        token = self._generate_jwt_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    async def _fetch_station_info(self) -> dict[str, Any]:
        """Fetch station information including sensors."""
        url = f"{API_BASE_URL}stations/{self.station_id}/current"
        headers = self._get_headers()

        async with self._session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()
            data = await response.json()

            # Cache station name
            if "name" in data:
                self.station_name = data["name"].get("SPANISH", "") or data["name"].get("BASQUE", "")

            # Cache sensor information
            if "sensors" in data:
                for sensor_info in data["sensors"]:
                    sensor_key = sensor_info.get("sensorKey", "").split("/")[-1]
                    if sensor_key:
                        self._station_sensors[sensor_key] = sensor_info

            return data

    async def _fetch_sensor_details(self, sensor_id: str) -> dict[str, Any]:
        """Fetch sensor details to get available measures."""
        url = f"{API_BASE_URL}sensors/{sensor_id}"
        headers = self._get_headers()

        async with self._session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _fetch_reading(
        self,
        sensor_id: str,
        measure_type: str,
        measure_id: str,
    ) -> float | None:
        """Fetch a specific reading from the API."""
        now = datetime.now(timezone.utc)
        year = now.year
        month = str(now.month).zfill(2)
        day = str(now.day).zfill(2)
        hour = str(now.hour).zfill(2)

        url = (
            f"{API_BASE_URL}readings/forStation/{self.station_id}/{sensor_id}/"
            f"measures/{measure_type}/{measure_id}/at/{year}/{month}/{day}/{hour}"
        )
        headers = self._get_headers()

        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Failed to fetch reading from %s: %s", url, response.status
                    )
                    return None

                data = await response.json()
                values = data.get("values", [])

                # Return the latest non-null value
                for value in reversed(values):
                    if value is not None:
                        return float(value)

                return None

        except Exception as err:
            _LOGGER.debug("Error fetching reading: %s", err)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Euskalmet API."""
        try:
            # First, get station information (if not cached)
            if not self._station_sensors:
                await self._fetch_station_info()

            # Fetch readings for each sensor type we're interested in
            processed_data = {
                "temperature": None,
                "humidity": None,
                "wind_speed": None,
                "wind_direction": None,
                "pressure": None,
                "precipitation": None,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

            # For each cached sensor, try to get readings
            for sensor_id, sensor_info in self._station_sensors.items():
                try:
                    # Get sensor details to know what measures it provides
                    sensor_details = await self._fetch_sensor_details(sensor_id)
                    meteors = sensor_details.get("meteors", [])

                    # Try to match sensors to our mappings
                    for meteor in meteors:
                        measure_type = meteor.get("measureType")
                        measure_id = meteor.get("measureId")

                        # Check if this matches any of our desired sensors
                        for sensor_type, mapping in SENSOR_MAPPINGS.items():
                            if (
                                measure_type == mapping["measureType"]
                                and measure_id == mapping["measure"]
                            ):
                                # Fetch the reading
                                value = await self._fetch_reading(
                                    sensor_id, measure_type, measure_id
                                )
                                if value is not None:
                                    processed_data[sensor_type] = value
                                    _LOGGER.debug(
                                        "Got %s = %s from sensor %s",
                                        sensor_type,
                                        value,
                                        sensor_id,
                                    )

                except Exception as err:
                    _LOGGER.debug(
                        "Error processing sensor %s: %s", sensor_id, err
                    )
                    continue

            _LOGGER.debug("Processed data: %s", processed_data)
            return processed_data

        except aiohttp.ClientResponseError as err:
            if err.status == 401 or err.status == 403:
                raise ConfigEntryAuthFailed("Invalid credentials") from err
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the aiohttp session."""
        await self._session.close()
