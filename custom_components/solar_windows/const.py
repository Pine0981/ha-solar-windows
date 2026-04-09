"""Constants for the Solar Windows integration."""

DOMAIN = "solar_windows"

CONF_WINDOWS = "windows"
CONF_WINDOW_NAME = "name"
CONF_WINDOW_FACING = "facing"
CONF_SUN_CONE = "sun_cone"
CONF_MIN_ELEVATION = "min_elevation"
CONF_WEATHER_ENTITY = "weather_entity"

DEFAULT_SUN_CONE = 65
DEFAULT_MIN_ELEVATION = 5
DEFAULT_WEATHER_ENTITY = "weather.home"

FACING_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

FACING_AZIMUTHS = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SW": 225,
    "W": 270,
    "NW": 315,
}

OVERCAST_STATES = ["cloudy", "rainy", "pouring", "snowy", "hail", "lightning", "lightning-rainy"]

ATTR_FACING = "facing"
ATTR_FACING_AZIMUTH = "facing_azimuth"
ATTR_SUN_AZIMUTH = "sun_azimuth"
ATTR_SUN_ELEVATION = "sun_elevation"
ATTR_AZIMUTH_DIFF = "azimuth_diff"
ATTR_WEATHER_STATE = "weather_state"
ATTR_SUN_CONE = "sun_cone_degrees"
