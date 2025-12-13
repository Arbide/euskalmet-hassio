"""Weather data coordinator for Euskalmet integration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp
import async_timeout
import jwt

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    API_WEATHER_FORECAST,
    API_WEATHER_TRENDS,
    API_WEATHER_HOURLY,
    API_WEATHER_REPORT,
    DOMAIN,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    JWT_VERSION,
    WEATHER_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class EuskalmetWeatherUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Euskalmet weather data."""

    def __init__(
        self,
        hass: HomeAssistant,
        private_key: str,
        fingerprint: str,
        region_id: str,
        zone_id: str,
        location_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_weather_{location_id}",
            update_interval=WEATHER_UPDATE_INTERVAL,
        )
        self.private_key = private_key
        self.fingerprint = fingerprint
        self.region_id = region_id
        self.zone_id = zone_id
        self.location_id = location_id
        self.session: aiohttp.ClientSession | None = None

    def _generate_jwt_token(self, hours: int = 1) -> str:
        """Generate JWT token for authentication."""
        now = datetime.now(timezone.utc)
        payload = {
            "aud": JWT_AUDIENCE,
            "iss": JWT_ISSUER,
            "exp": int((now + timedelta(hours=hours)).timestamp()),
            "version": JWT_VERSION,
            "iat": int(now.timestamp()),
            "loginId": self.fingerprint,
        }
        token = jwt.encode(payload, self.private_key, algorithm=JWT_ALGORITHM)
        return token

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        token = self._generate_jwt_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _fetch_json(self, url: str) -> dict[str, Any] | None:
        """Fetch JSON data from URL."""
        session = await self._get_session()
        headers = self._get_headers()

        try:
            async with async_timeout.timeout(30):
                async with session.get(url, headers=headers) as response:
                    if response.status in (401, 403):
                        raise ConfigEntryAuthFailed("Invalid credentials")

                    if response.status != 200:
                        text = await response.text()
                        _LOGGER.warning(
                            "Error fetching data from %s: %s - %s",
                            url,
                            response.status,
                            text[:200],
                        )
                        return None

                    return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error fetching %s: %s", url, err)
            raise UpdateFailed(f"Network error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching %s: %s", url, err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _fetch_current_weather(self, now: datetime) -> dict[str, Any] | None:
        """Fetch current weather conditions from reports endpoint."""
        url = (
            f"{API_BASE_URL}"
            f"{API_WEATHER_REPORT.format(region_id=self.region_id, zone_id=self.zone_id, location_id=self.location_id, year=now.year, month=now.month, day=now.day)}"
        )

        _LOGGER.debug("Fetching current weather from: %s", url)
        data = await self._fetch_json(url)

        if not data or "report" not in data:
            _LOGGER.warning("No current weather data found")
            return None

        report = data["report"]

        # Extract current conditions
        current = {}

        # Temperature
        if "temperature" in report and report["temperature"]:
            current["temperature"] = report["temperature"].get("value")

        # Humidity
        if "humidity" in report and report["humidity"]:
            current["humidity"] = report["humidity"].get("value")

        # Pressure - Not available in reports endpoint for locations
        if "pressure" in report and report["pressure"]:
            current["pressure"] = report["pressure"].get("value")

        # Wind speed - API incorrectly uses "winddirection" field for wind speed in km/h
        # We need to convert from km/h to m/s
        if "winddirection" in report and report["winddirection"]:
            wind_speed_kmh = report["winddirection"].get("value")
            if wind_speed_kmh is not None:
                # Convert km/h to m/s (divide by 3.6)
                current["wind_speed"] = wind_speed_kmh / 3.6

        # Wind direction - Not available in reports endpoint for locations
        # The "windspeed" field (if it exists) might contain direction, but typically not present
        if "windspeed" in report and report["windspeed"]:
            current["wind_direction"] = report["windspeed"].get("value")

        # Precipitation (accumulated)
        if "precipitationAccumulated" in report and report["precipitationAccumulated"]:
            # Get most recent accumulated value (use 60-minute period if available)
            precip_data = report["precipitationAccumulated"]
            if isinstance(precip_data, list) and len(precip_data) > 0:
                # Try to find 60-minute period first, otherwise use last item
                precip_item = None
                for item in precip_data:
                    if isinstance(item, dict) and item.get("period") == 60:
                        precip_item = item
                        break

                # If no 60-minute period found, use the last item
                if not precip_item:
                    precip_item = precip_data[-1]

                # Extract nested value structure: precipitationAccumulated[i]["value"]["value"]
                if isinstance(precip_item, dict) and "value" in precip_item:
                    precip_value = precip_item["value"]
                    if isinstance(precip_value, dict) and "value" in precip_value:
                        precip_mm = precip_value["value"]
                        current["precipitation"] = precip_mm
                        _LOGGER.debug("Precipitation extracted: %s mm", precip_mm)

        return current

    async def _fetch_forecast_daily(self, now: datetime) -> list[dict[str, Any]] | None:
        """Fetch daily forecast from trends endpoint."""
        url = (
            f"{API_BASE_URL}"
            f"{API_WEATHER_TRENDS.format(region_id=self.region_id, zone_id=self.zone_id, location_id=self.location_id, year=now.year, month=now.month, day=now.day, for_year=now.year, for_month=now.month, for_day=now.day)}"
        )

        _LOGGER.debug("Fetching daily forecast from: %s", url)
        data = await self._fetch_json(url)

        if not data or "trendsByDate" not in data:
            _LOGGER.warning("No daily forecast data found")
            return None

        trends_by_date = data["trendsByDate"]
        if "set" not in trends_by_date:
            return None

        trends = trends_by_date["set"]
        _LOGGER.info("Daily forecast API returned %d days total", len(trends))

        forecasts = []
        # Use local date for comparison (not UTC)
        today = datetime.now().date()
        skipped_past = 0
        skipped_no_condition = 0

        for trend in trends:
            # Date - check first and skip past days
            if "date" not in trend:
                continue

            # Skip past days (only include today and future days)
            try:
                # Parse the date from the API (comes as "2025-12-13T23:00:00Z" which is UTC)
                forecast_datetime_utc = datetime.fromisoformat(trend["date"].replace('Z', '+00:00'))

                # Convert UTC to local time to get the correct date
                # UTC datetime is timezone-aware, need to convert to local
                from datetime import timezone as dt_timezone
                local_datetime = forecast_datetime_utc.replace(tzinfo=dt_timezone.utc).astimezone(tz=None)
                forecast_date = local_datetime.date()

                _LOGGER.debug("UTC: %s -> Local: %s (date: %s) vs today: %s",
                             trend["date"], local_datetime, forecast_date, today)

                if forecast_date < today:
                    _LOGGER.info("Skipping past day: %s (UTC: %s)", forecast_date, trend["date"])
                    skipped_past += 1
                    continue
            except (ValueError, AttributeError) as err:
                _LOGGER.warning("Could not parse date %s: %s", trend.get("date"), err)
                continue

            forecast = {}
            forecast["datetime"] = trend["date"]

            # Temperature range
            if "temperatureRange" in trend:
                temp_range = trend["temperatureRange"]
                if "max" in temp_range:
                    forecast["temperature"] = temp_range["max"]
                if "min" in temp_range:
                    forecast["temperature_low"] = temp_range["min"]

            # Weather condition
            has_condition = False
            if "weather" in trend and trend["weather"]:
                weather = trend["weather"]
                if "id" in weather:
                    forecast["condition_code"] = weather["id"]
                    has_condition = True

            # Add to list if has essential data
            if "datetime" in forecast and "condition_code" in forecast:
                forecasts.append(forecast)
            elif not has_condition:
                _LOGGER.warning("Skipping day %s - no condition_code", forecast.get("datetime"))
                skipped_no_condition += 1

        _LOGGER.info("Daily forecast processing: skipped %d past days, %d without condition",
                    skipped_past, skipped_no_condition)

        # Sort by datetime (earliest first)
        if forecasts:
            forecasts.sort(key=lambda x: x["datetime"])
            _LOGGER.info("Daily forecast: returning %d days, first day: %s", len(forecasts), forecasts[0].get("datetime") if forecasts else "none")
        else:
            _LOGGER.warning("Daily forecast: no forecasts found after filtering")

        return forecasts if forecasts else None

    async def _fetch_forecast_hourly(self, now: datetime) -> list[dict[str, Any]] | None:
        """Fetch hourly forecast from trends/measures endpoint for today and tomorrow."""
        all_forecasts = []

        # Fetch hourly forecast for today and tomorrow to get full 24 hours
        for day_offset in [0, 1]:
            target_date = now + timedelta(days=day_offset)

            url = (
                f"{API_BASE_URL}"
                f"{API_WEATHER_HOURLY.format(region_id=self.region_id, zone_id=self.zone_id, location_id=self.location_id, year=now.year, month=now.month, day=now.day, for_year=target_date.year, for_month=target_date.month, for_day=target_date.day)}"
            )

            _LOGGER.debug("Fetching hourly forecast from: %s", url)
            data = await self._fetch_json(url)

            if not data or "trends" not in data:
                _LOGGER.warning("No hourly forecast data found for day offset %s", day_offset)
                continue

            trends_data = data["trends"]
            if "set" not in trends_data:
                continue

            measures = trends_data["set"]

            for measure in measures:
                forecast = {}

                # Time range - parse to get datetime
                if "range" in measure:
                    # Format: "LocalTime:[HH:00:00:000..HH:59:59:999]"
                    time_range = measure["range"]
                    try:
                        # Extract hour from range
                        hour_str = time_range.split("[")[1].split(":")[0]
                        hour = int(hour_str)

                        # Create datetime for this hour using the target date
                        forecast_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                        forecast["datetime"] = forecast_time.isoformat()
                    except (IndexError, ValueError) as err:
                        _LOGGER.warning("Could not parse time range %s: %s", time_range, err)
                        continue

                # Temperature
                if "temperature" in measure and measure["temperature"]:
                    forecast["temperature"] = measure["temperature"].get("value")

                # Precipitation
                if "precipitation" in measure and measure["precipitation"]:
                    forecast["precipitation"] = measure["precipitation"].get("value")

                # Wind speed
                if "windspeed" in measure and measure["windspeed"]:
                    forecast["wind_speed"] = measure["windspeed"].get("value")

                # Wind direction
                if "winddirection" in measure and measure["winddirection"]:
                    forecast["wind_direction"] = measure["winddirection"].get("value")

                # Humidity
                if "humidity" in measure and measure["humidity"]:
                    forecast["humidity"] = measure["humidity"].get("value")

                # Pressure
                if "pressure" in measure and measure["pressure"]:
                    forecast["pressure"] = measure["pressure"].get("value")

                # Weather condition from symbolSet
                if "symbolSet" in measure and measure["symbolSet"]:
                    symbol_set = measure["symbolSet"]
                    if "weather" in symbol_set and symbol_set["weather"]:
                        weather = symbol_set["weather"]
                        if "id" in weather:
                            forecast["condition_code"] = weather["id"]

                # Precipitation probability (if available)
                if "precipitationProbability" in measure and measure["precipitationProbability"]:
                    forecast["precipitation_probability"] = measure["precipitationProbability"].get("value")

                # Add to list if has essential data
                if "datetime" in forecast and "condition_code" in forecast:
                    all_forecasts.append(forecast)

        # Sort by datetime (earliest first)
        if all_forecasts:
            all_forecasts.sort(key=lambda x: x["datetime"])

        return all_forecasts if all_forecasts else None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        now = datetime.now(timezone.utc)

        _LOGGER.debug(
            "Updating weather data for %s (%s/%s)",
            self.location_id,
            self.region_id,
            self.zone_id,
        )

        # Fetch all data in parallel
        current = await self._fetch_current_weather(now)
        forecast_daily = await self._fetch_forecast_daily(now)
        forecast_hourly = await self._fetch_forecast_hourly(now)

        # If we have no current data at all, raise an error
        if not current:
            raise UpdateFailed("No current weather data available")

        return {
            "current": current,
            "forecast_daily": forecast_daily,
            "forecast_hourly": forecast_hourly,
            "last_update": now.isoformat(),
        }

    async def async_shutdown(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
