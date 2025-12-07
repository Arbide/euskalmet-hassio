"""Constants for the Euskalmet integration."""
from datetime import timedelta
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfIrradiance,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPrecipitationDepth,
)

DOMAIN: Final = "euskalmet"
DEFAULT_NAME: Final = "Euskalmet"
ATTRIBUTION: Final = "Data provided by Euskalmet"

# Configuration
CONF_STATION = "station"
CONF_PRIVATE_KEY = "private_key"
CONF_FINGERPRINT = "fingerprint"

# JWT Configuration
JWT_ISSUER: Final = "euskalmet-hassio"
JWT_AUDIENCE: Final = "met01.apikey"
JWT_VERSION: Final = "1.0.0"
JWT_ALGORITHM: Final = "RS256"

# Update intervals (fetch data every 10 minutes)
UPDATE_INTERVAL = timedelta(minutes=10)
SCAN_INTERVAL = timedelta(minutes=10)

# API endpoints
API_BASE_URL: Final = "https://api.euskadi.eus/euskalmet/"
API_STATIONS: Final = "stations"
API_MEASURES: Final = "measures"
API_READINGS: Final = "readings"
API_SENSORS: Final = "sensors"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_WIND_SPEED = "wind_speed"
SENSOR_WIND_SPEED_MAX = "wind_speed_max"
SENSOR_WIND_DIRECTION = "wind_direction"
SENSOR_PRESSURE = "pressure"
SENSOR_PRECIPITATION = "precipitation"
SENSOR_IRRADIANCE = "irradiance"

# Sensor definitions
SENSOR_TYPES: Final[dict[str, dict]] = {
    SENSOR_TEMPERATURE: {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
        "suggested_display_precision": 1,
    },
    SENSOR_HUMIDITY: {
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:water-percent",
        "suggested_display_precision": 0,
    },
    SENSOR_WIND_SPEED: {
        "name": "Wind Speed",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.METERS_PER_SECOND,
        "icon": "mdi:weather-windy",
        "suggested_display_precision": 1,
    },
    SENSOR_WIND_SPEED_MAX: {
        "name": "Wind Speed Max",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.METERS_PER_SECOND,
        "icon": "mdi:weather-windy-variant",
        "suggested_display_precision": 1,
    },
    SENSOR_WIND_DIRECTION: {
        "name": "Wind Direction",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": DEGREE,
        "icon": "mdi:compass",
        "suggested_display_precision": 0,
    },
    SENSOR_PRESSURE: {
        "name": "Pressure",
        "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPressure.HPA,
        "icon": "mdi:gauge",
        "suggested_display_precision": 1,
    },
    SENSOR_PRECIPITATION: {
        "name": "Precipitation",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfPrecipitationDepth.MILLIMETERS,
        "icon": "mdi:weather-rainy",
        "suggested_display_precision": 1,
    },
    SENSOR_IRRADIANCE: {
        "name": "Solar Irradiance",
        "device_class": SensorDeviceClass.IRRADIANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        "icon": "mdi:white-balance-sunny",
        "suggested_display_precision": 0,
    },
}
