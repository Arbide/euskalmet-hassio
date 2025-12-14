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
# Based on actual Euskalmet API response
SENSOR_MAPPINGS = {
    "temperature": {"measureType": "measuresForAir", "measure": "temperature"},
    "humidity": {"measureType": "measuresForAir", "measure": "humidity"},
    "wind_speed": {"measureType": "measuresForWind", "measure": "mean_speed"},
    "wind_speed_max": {"measureType": "measuresForWind", "measure": "max_speed"},
    "wind_direction": {"measureType": "measuresForWind", "measure": "mean_direction"},
    "pressure": {"measureType": "measuresForAtmosphere", "measure": "pressure"},
    "precipitation": {"measureType": "measuresForWater", "measure": "precipitation"},
    "irradiance": {"measureType": "measuresForSun", "measure": "irradiance"},
    "sheet_level_1": {"measureType": "measuresForWater", "measure": "sheet_level_1"},
    "sheet_level_2": {"measureType": "measuresForWater", "measure": "sheet_level_2"},
    "sheet_level_3": {"measureType": "measuresForWater", "measure": "sheet_level_3"},
    "flow_1_computed": {"measureType": "measuresForWater", "measure": "flow_1_computed"},
    "flow_2_computed": {"measureType": "measuresForWater", "measure": "flow_2_computed"},
    "max_wave_height": {"measureType": "measuresForWaves", "measure": "max_wave_height"},
    "significant_height": {"measureType": "measuresForWaves", "measure": "significant_height"},
    "surf_period": {"measureType": "measuresForWaves", "measure": "surf_period"},
    "peak_period": {"measureType": "measuresForWaves", "measure": "peak_period"},
    "speed_sigma": {"measureType": "measuresForWind", "measure": "speed_sigma"},
    "direction_sigma": {"measureType": "measuresForWind", "measure": "direction_sigma"},
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
        self.available_sensor_types = set()  # Types of sensors available in this station

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        _LOGGER.info(
            "Euskalmet coordinator initialized with update interval: %s (%.0f minutes)",
            UPDATE_INTERVAL,
            UPDATE_INTERVAL.total_seconds() / 60,
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

        try:
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
                    sensor_count = 0
                    for sensor_info in data["sensors"]:
                        sensor_key = sensor_info.get("sensorKey", "").split("/")[-1]
                        if sensor_key:
                            self._station_sensors[sensor_key] = sensor_info
                            sensor_count += 1

                    _LOGGER.info(
                        "Station %s initialized: '%s' with %d sensors",
                        self.station_id, self.station_name, sensor_count
                    )
                else:
                    _LOGGER.warning(
                        "Station %s has no sensors configured",
                        self.station_id
                    )

                return data
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Network error fetching station info for %s: %s",
                self.station_id, err
            )
            raise
        except Exception as err:
            _LOGGER.error(
                "Unexpected error fetching station info for %s: %s",
                self.station_id, err, exc_info=True
            )
            raise

    async def _fetch_sensor_details(self, sensor_id: str) -> dict[str, Any]:
        """Fetch sensor details to get available measures."""
        url = f"{API_BASE_URL}sensors/{sensor_id}"
        headers = self._get_headers()

        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Network error fetching details for sensor '%s' from station %s: %s",
                sensor_id, self.station_id, err
            )
            raise
        except Exception as err:
            _LOGGER.error(
                "Unexpected error fetching details for sensor '%s' from station %s: %s",
                sensor_id, self.station_id, err, exc_info=True
            )
            raise

    async def _fetch_reading(
        self,
        sensor_id: str,
        measure_type: str,
        measure_id: str,
    ) -> float | None:
        """Fetch a specific reading from the API."""
        now = datetime.now(timezone.utc) - timedelta(minutes=10)
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
                    _LOGGER.warning(
                        "Failed to fetch reading for sensor '%s' (measure: %s/%s) from station %s: HTTP %s. URL: %s",
                        sensor_id, measure_type, measure_id, self.station_id, response.status, url
                    )
                    return None

                data = await response.json()
                values = data.get("values", [])

                # Return the latest non-null value
                for value in reversed(values):
                    if value is not None:
                        return float(value)

                # All values were None
                _LOGGER.warning(
                    "No valid data available for sensor '%s' (measure: %s/%s) from station %s. API returned all null values.",
                    sensor_id, measure_type, measure_id, self.station_id
                )
                return None

        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Network error fetching reading for sensor '%s' (measure: %s/%s) from station %s: %s",
                sensor_id, measure_type, measure_id, self.station_id, err
            )
            return None
        except Exception as err:
            _LOGGER.error(
                "Unexpected error fetching reading for sensor '%s' (measure: %s/%s) from station %s: %s",
                sensor_id, measure_type, measure_id, self.station_id, err, exc_info=True
            )
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Euskalmet API."""
        _LOGGER.debug("Starting data update for station %s", self.station_id)
        try:
            # First, get station information (if not cached)
            if not self._station_sensors:
                await self._fetch_station_info()

            # Fetch readings for each sensor type we're interested in
            processed_data = {
                "temperature": None,
                "humidity": None,
                "wind_speed": None,
                "wind_speed_max": None,
                "wind_direction": None,
                "pressure": None,
                "precipitation": None,
                "irradiance": None,
                "sheet_level_1": None,
                "sheet_level_2": None,
                "sheet_level_3": None,
                "flow_1_computed": None,
                "flow_2_computed": None,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

            # For each cached sensor, try to get readings
            for sensor_id, sensor_info in self._station_sensors.items():
                try:
                    # Get sensor details to know what measures it provides
                    sensor_details = await self._fetch_sensor_details(sensor_id)
                    meteors = sensor_details.get("meteors", [])

                    # Log all available meteors for debugging
                    _LOGGER.debug(
                        "Sensor %s has meteors: %s",
                        sensor_id,
                        [(m.get("measureType"), m.get("measureId")) for m in meteors]
                    )

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
                                    self.available_sensor_types.add(sensor_type)
                                    _LOGGER.debug(
                                        "Got %s = %s from sensor %s",
                                        sensor_type,
                                        value,
                                        sensor_id,
                                    )
                                else:
                                    _LOGGER.info(
                                        "Sensor type '%s' returned no data (sensor: %s, measure: %s/%s)",
                                        sensor_type, sensor_id, measure_type, measure_id
                                    )

                except Exception as err:
                    _LOGGER.error(
                        "Error processing sensor %s from station %s: %s",
                        sensor_id, self.station_id, err, exc_info=True
                    )
                    continue

            # Log summary of data collection
            successful_sensors = [k for k, v in processed_data.items() if v is not None and k != "last_update"]
            failed_sensors = [k for k, v in processed_data.items() if v is None and k != "last_update"]

            if failed_sensors:
                _LOGGER.warning(
                    "Data update for station %s completed with missing data. Successfully retrieved: %s. Missing: %s",
                    self.station_id, successful_sensors or "none", failed_sensors
                )
            else:
                _LOGGER.info(
                    "Data update completed successfully for station %s. All sensors retrieved: %s. Next update in %.0f minutes",
                    self.station_id, successful_sensors, UPDATE_INTERVAL.total_seconds() / 60
                )

            _LOGGER.debug("Processed data: %s", processed_data)
            return processed_data

        except aiohttp.ClientResponseError as err:
            if err.status == 401 or err.status == 403:
                _LOGGER.error(
                    "Authentication failed for station %s: HTTP %s. Please check your credentials.",
                    self.station_id, err.status
                )
                raise ConfigEntryAuthFailed("Invalid credentials") from err
            _LOGGER.error(
                "API error for station %s: HTTP %s - %s",
                self.station_id, err.status, err
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Network error communicating with API for station %s: %s",
                self.station_id, err
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error(
                "Unexpected error updating data for station %s: %s",
                self.station_id, err, exc_info=True
            )
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the aiohttp session."""
        await self._session.close()
