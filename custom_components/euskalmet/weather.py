"""Weather platform for Euskalmet integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPrecipitationDepth,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sun import get_astral_location
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_LOCATION,
    DOMAIN,
    WEATHER_CONDITION_MAP,
)
from .weather_coordinator import EuskalmetWeatherUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Euskalmet weather entity."""
    coordinator: EuskalmetWeatherUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get location info from entry data
    location_id = entry.data[CONF_LOCATION]
    location_name = entry.data.get("location_name", location_id)
    region_id = entry.data.get("region_id", "unknown")
    zone_id = entry.data.get("zone_id", "unknown")

    async_add_entities(
        [EuskalmetWeatherEntity(coordinator, location_id, location_name, region_id, zone_id)]
    )


class EuskalmetWeatherEntity(
    CoordinatorEntity[EuskalmetWeatherUpdateCoordinator], WeatherEntity
):
    """Representation of an Euskalmet weather entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        coordinator: EuskalmetWeatherUpdateCoordinator,
        location_id: str,
        location_name: str,
        region_id: str,
        zone_id: str,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)

        self.location_id = location_id
        self.location_name = location_name
        self.region_id = region_id
        self.zone_id = zone_id

        # Entity attributes
        self._attr_unique_id = f"{DOMAIN}_weather_{location_id}"
        self._attr_name = None  # Use device name

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"location_{location_id}")},
            name=f"Euskalmet {location_name}",
            manufacturer="Euskalmet",
            model="Weather Forecast",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        current = self.coordinator.data["current"]

        # Try to get condition from current data
        condition_code = current.get("condition_code")

        if not condition_code:
            # Get condition from hourly forecast for current or next closest hour
            forecast_hourly = self.coordinator.data.get("forecast_hourly")
            if forecast_hourly and len(forecast_hourly) > 0:
                now = datetime.now()

                # Find the forecast for current hour or next closest hour
                for forecast in forecast_hourly:
                    forecast_time_str = forecast.get("datetime")
                    if forecast_time_str:
                        try:
                            forecast_time = datetime.fromisoformat(forecast_time_str.replace('Z', '+00:00'))
                            # Use forecast if it's for current hour or later
                            if forecast_time.hour >= now.hour:
                                condition_code = forecast.get("condition_code")
                                break
                        except (ValueError, AttributeError):
                            continue

                # If no future forecast found, use the first available
                if not condition_code and len(forecast_hourly) > 0:
                    condition_code = forecast_hourly[0].get("condition_code")

        if not condition_code:
            return None

        return self._map_condition(condition_code)

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature in °C."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        return self.coordinator.data["current"].get("temperature")

    @property
    def native_temperature_high(self) -> float | None:
        """Return today's high temperature in °C."""
        if not self.coordinator.data or "forecast_daily" not in self.coordinator.data:
            return None

        forecast_daily = self.coordinator.data["forecast_daily"]
        if not forecast_daily or len(forecast_daily) == 0:
            return None

        # Find today's forecast by matching the date
        today = datetime.now().date()
        for day_forecast in forecast_daily:
            try:
                forecast_date_str = day_forecast.get("datetime")
                if forecast_date_str:
                    # Convert UTC to local time before comparing dates
                    from datetime import timezone as dt_timezone
                    forecast_datetime_utc = datetime.fromisoformat(forecast_date_str.replace('Z', '+00:00'))
                    local_datetime = forecast_datetime_utc.replace(tzinfo=dt_timezone.utc).astimezone(tz=None)
                    forecast_date = local_datetime.date()

                    if forecast_date == today:
                        return day_forecast.get("temperature")
            except (ValueError, AttributeError):
                continue

        # Fallback: use first day if today not found
        return forecast_daily[0].get("temperature")

    @property
    def native_temperature_low(self) -> float | None:
        """Return today's low temperature in °C."""
        if not self.coordinator.data or "forecast_daily" not in self.coordinator.data:
            return None

        forecast_daily = self.coordinator.data["forecast_daily"]
        if not forecast_daily or len(forecast_daily) == 0:
            return None

        # Find today's forecast by matching the date
        today = datetime.now().date()
        for day_forecast in forecast_daily:
            try:
                forecast_date_str = day_forecast.get("datetime")
                if forecast_date_str:
                    # Convert UTC to local time before comparing dates
                    from datetime import timezone as dt_timezone
                    forecast_datetime_utc = datetime.fromisoformat(forecast_date_str.replace('Z', '+00:00'))
                    local_datetime = forecast_datetime_utc.replace(tzinfo=dt_timezone.utc).astimezone(tz=None)
                    forecast_date = local_datetime.date()

                    if forecast_date == today:
                        return day_forecast.get("temperature_low")
            except (ValueError, AttributeError):
                continue

        # Fallback: use first day if today not found
        return forecast_daily[0].get("temperature_low")

    @property
    def humidity(self) -> int | None:
        """Return the current humidity in %."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        humidity = self.coordinator.data["current"].get("humidity")
        if humidity is not None:
            return int(humidity)
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure in hPa."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        return self.coordinator.data["current"].get("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        """Return the current wind speed in m/s."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        return self.coordinator.data["current"].get("wind_speed")

    @property
    def wind_bearing(self) -> int | None:
        """Return the current wind bearing in degrees (0-360)."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        wind_direction = self.coordinator.data["current"].get("wind_direction")
        if wind_direction is not None:
            return int(wind_direction)
        return None

    @property
    def native_precipitation(self) -> float | None:
        """Return the current precipitation in mm."""
        if not self.coordinator.data or "current" not in self.coordinator.data:
            return None

        return self.coordinator.data["current"].get("precipitation")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast."""
        if not self.coordinator.data or "forecast_daily" not in self.coordinator.data:
            return None

        forecast_data = self.coordinator.data["forecast_daily"]
        if not forecast_data:
            return None

        forecasts = []
        for item in forecast_data:
            try:
                forecast = Forecast(
                    datetime=item["datetime"],
                    native_temperature=item.get("temperature"),
                    native_templow=item.get("temperature_low"),
                    condition=self._map_condition(item.get("condition_code")),  # No day/night for daily
                    native_precipitation=item.get("precipitation"),
                    precipitation_probability=item.get("precipitation_probability"),
                    humidity=item.get("humidity"),
                    native_pressure=item.get("pressure"),
                    native_wind_speed=item.get("wind_speed"),
                    wind_bearing=int(item["wind_direction"])
                    if item.get("wind_direction") is not None
                    else None,
                )
                forecasts.append(forecast)
            except (KeyError, ValueError) as err:
                _LOGGER.warning("Error parsing daily forecast item: %s", err)
                continue

        if forecasts:
            _LOGGER.debug("Weather entity daily forecast: returning %d days", len(forecasts))

        return forecasts if forecasts else None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast."""
        if not self.coordinator.data or "forecast_hourly" not in self.coordinator.data:
            return None

        forecast_data = self.coordinator.data["forecast_hourly"]
        if not forecast_data:
            return None

        # Get current time
        now = datetime.now()

        forecasts = []
        for item in forecast_data:
            try:
                # Parse forecast datetime
                forecast_time_str = item.get("datetime")
                if not forecast_time_str:
                    continue

                forecast_time = datetime.fromisoformat(forecast_time_str.replace('Z', '+00:00'))
                forecast_time_naive = forecast_time.replace(tzinfo=None)

                # Only include forecasts for current or future hours
                # Skip if the forecast hour is in the past (comparing full datetime, but with hour precision)
                if forecast_time_naive.replace(minute=0, second=0, microsecond=0) < now.replace(minute=0, second=0, microsecond=0):
                    continue

                # Parse datetime for day/night detection
                forecast_datetime = None
                try:
                    forecast_datetime = datetime.fromisoformat(item["datetime"].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

                forecast = Forecast(
                    datetime=item["datetime"],
                    native_temperature=item.get("temperature"),
                    condition=self._map_condition(item.get("condition_code"), forecast_datetime),
                    native_precipitation=item.get("precipitation"),
                    precipitation_probability=item.get("precipitation_probability"),
                    humidity=item.get("humidity"),
                    native_pressure=item.get("pressure"),
                    native_wind_speed=item.get("wind_speed"),
                    wind_bearing=int(item["wind_direction"])
                    if item.get("wind_direction") is not None
                    else None,
                )
                forecasts.append(forecast)

                # Limit to next 24 hours
                if len(forecasts) >= 24:
                    break

            except (KeyError, ValueError) as err:
                _LOGGER.warning("Error parsing hourly forecast item: %s", err)
                continue

        return forecasts if forecasts else None

    def _is_night(self, check_time: datetime | None = None) -> bool:
        """Check if given time is during night (after sunset or before sunrise)."""
        if check_time is None:
            check_time = datetime.now()

        # Remove timezone info for comparison
        check_time = check_time.replace(tzinfo=None)

        try:
            # Get location for sun calculations
            location = get_astral_location(self.hass)

            # Get sunrise and sunset for the check date
            sunrise = location.sunrise(check_time, local=True).replace(tzinfo=None)
            sunset = location.sunset(check_time, local=True).replace(tzinfo=None)

            # It's night if before sunrise or after sunset
            return check_time < sunrise or check_time > sunset
        except Exception:
            # Fallback to simple hour check if astral calculation fails
            return check_time.hour < 6 or check_time.hour >= 20

    def _map_condition(self, euskalmet_code: str | None, forecast_time: datetime | None = None) -> str:
        """Map Euskalmet condition code to HA standard, with day/night variants."""
        if not euskalmet_code:
            return "exceptional"

        is_night = self._is_night(forecast_time)

        # Handle day/night variants for clear/sunny conditions
        if euskalmet_code == "00":
            return "clear-night" if is_night else "sunny"

        # Handle day/night variants for partly cloudy conditions
        if euskalmet_code in ("01", "02"):
            return "partlycloudy" if not is_night else "partlycloudy"  # HA doesn't have night variant for this

        # Get base mapping
        mapped = WEATHER_CONDITION_MAP.get(euskalmet_code)
        if not mapped:
            _LOGGER.warning(
                "Unknown weather condition code: %s, using 'exceptional'",
                euskalmet_code,
            )
            return "exceptional"

        return mapped
