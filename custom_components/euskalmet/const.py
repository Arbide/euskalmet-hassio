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
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPrecipitationDepth,
    UnitOfVolumeFlowRate,
)

DOMAIN: Final = "euskalmet"
DEFAULT_NAME: Final = "Euskalmet"
ATTRIBUTION: Final = "Data provided by Euskalmet"

# Configuration
CONF_STATION = "station"
CONF_LOCATION = "location"
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

# Weather update interval (longer than sensors - weather forecasts don't change as frequently)
WEATHER_UPDATE_INTERVAL = timedelta(minutes=30)

# API endpoints
API_BASE_URL: Final = "https://api.euskadi.eus/euskalmet/"
API_STATIONS: Final = "stations"
API_MEASURES: Final = "measures"
API_READINGS: Final = "readings"
API_SENSORS: Final = "sensors"

# Weather API endpoints
API_GEO_REGIONS: Final = "geo/regions"
API_GEO_ZONES: Final = "geo/regions/{region_id}/zones"
API_GEO_LOCATIONS: Final = "geo/regions/{region_id}/zones/{zone_id}/locations"
API_WEATHER_FORECAST: Final = "weather/regions/{region_id}/zones/{zone_id}/locations/{location_id}/forecast/at/{year}/{month:02d}/{day:02d}/for/{for_year}{for_month:02d}{for_day:02d}"
API_WEATHER_TRENDS: Final = "weather/regions/{region_id}/zones/{zone_id}/locations/{location_id}/forecast/trends/at/{year}/{month:02d}/{day:02d}/for/{for_year}{for_month:02d}{for_day:02d}"
API_WEATHER_HOURLY: Final = "weather/regions/{region_id}/zones/{zone_id}/locations/{location_id}/forecast/trends/measures/at/{year}/{month:02d}/{day:02d}/for/{for_year}{for_month:02d}{for_day:02d}"
API_WEATHER_REPORT: Final = "weather/regions/{region_id}/zones/{zone_id}/locations/{location_id}/reports/for/{year}/{month:02d}/{day:02d}/last"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_WIND_SPEED = "wind_speed"
SENSOR_WIND_SPEED_MAX = "wind_speed_max"
SENSOR_WIND_DIRECTION = "wind_direction"
SENSOR_PRESSURE = "pressure"
SENSOR_PRECIPITATION = "precipitation"
SENSOR_IRRADIANCE = "irradiance"
SENSOR_SHEET_LEVEL_1 = "sheet_level_1"
SENSOR_SHEET_LEVEL_2 = "sheet_level_2"
SENSOR_SHEET_LEVEL_3 = "sheet_level_3"
SENSOR_FLOW_1 = "flow_1_computed"
SENSOR_FLOW_2 = "flow_2_computed"

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
    SENSOR_SHEET_LEVEL_1: {
        "name": "Water Level 1",
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfLength.METERS,
        "icon": "mdi:waves",
        "suggested_display_precision": 2,
    },
    SENSOR_SHEET_LEVEL_2: {
        "name": "Water Level 2",
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfLength.METERS,
        "icon": "mdi:waves",
        "suggested_display_precision": 2,
    },
    SENSOR_SHEET_LEVEL_3: {
        "name": "Water Level 3",
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfLength.METERS,
        "icon": "mdi:waves",
        "suggested_display_precision": 2,
    },
    SENSOR_FLOW_1: {
        "name": "Flow Rate 1",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
        "icon": "mdi:waves-arrow-right",
        "suggested_display_precision": 2,
    },
    SENSOR_FLOW_2: {
        "name": "Flow Rate 2",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
        "icon": "mdi:waves-arrow-right",
        "suggested_display_precision": 2,
    },
}

# Weather condition mapping from Euskalmet codes to Home Assistant standard conditions
# Based on API exploration and Euskalmet icon codes
# Reference: https://www.euskalmet.euskadi.eus/media/assets/icons/euskalmet/
WEATHER_CONDITION_MAP: Final[dict[str, str]] = {
    # Clear / Despejado
    "00": "sunny",  # Despejado / Oskarbi (day will be handled by entity)

    # Cloudy / Nuboso
    "01": "partlycloudy",  # Poco nuboso / Hodei gutxi
    "02": "partlycloudy",  # Nuboso / Partially cloudy
    "03": "cloudy",  # Muy nuboso / Very cloudy
    "04": "cloudy",  # Cubierto / Overcast

    # Fog / Niebla
    "05": "fog",  # Niebla / Fog
    "06": "fog",  # Niebla dispersa / Scattered fog
    "07": "fog",  # Niebla en bancos / Fog banks
    "08": "fog",  # Niebla y niebla helada / Fog and freezing fog
    "09": "fog",  # Bruma / Mist

    # Rain / Lluvia
    "10": "rainy",  # Chubascos débiles / Zaparrada txikiak (light showers)
    "11": "rainy",  # Chubascos / Showers
    "12": "rainy",  # Lluvia débil / Euri txikia (light rain)
    "13": "rainy",  # Lluvia / Rain
    "14": "pouring",  # Lluvia fuerte / Heavy rain

    # Snow / Nieve
    "15": "snowy",  # Nieve débil / Light snow
    "16": "snowy",  # Nieve / Snow
    "17": "snowy",  # Nieve fuerte / Heavy snow

    # Storms / Tormentas
    "18": "lightning",  # Tormenta débil / Light storm
    "19": "lightning-rainy",  # Tormenta / Storm
    "20": "lightning-rainy",  # Tormenta fuerte / Heavy storm

    # Mixed / Mezclado
    "21": "snowy-rainy",  # Aguanieve / Sleet
    "22": "hail",  # Granizo / Hail

    # Wind / Viento
    "23": "windy",  # Viento fuerte / Strong wind
    "24": "exceptional",  # Viento muy fuerte / Very strong wind
}
