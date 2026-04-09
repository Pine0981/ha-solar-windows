"""Binary sensor platform for Solar Windows."""
from __future__ import annotations

import logging
import math
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_WINDOWS,
    CONF_WINDOW_NAME,
    CONF_WINDOW_FACING,
    CONF_SUN_CONE,
    CONF_MIN_ELEVATION,
    CONF_WEATHER_ENTITY,
    DEFAULT_SUN_CONE,
    DEFAULT_MIN_ELEVATION,
    DEFAULT_WEATHER_ENTITY,
    FACING_AZIMUTHS,
    OVERCAST_STATES,
    ATTR_FACING,
    ATTR_FACING_AZIMUTH,
    ATTR_SUN_AZIMUTH,
    ATTR_SUN_ELEVATION,
    ATTR_AZIMUTH_DIFF,
    ATTR_WEATHER_STATE,
    ATTR_SUN_CONE,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=2)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Windows binary sensors from config entry."""
    data = entry.data
    windows = data.get(CONF_WINDOWS, [])
    sun_cone = float(data.get(CONF_SUN_CONE, DEFAULT_SUN_CONE))
    min_elevation = float(data.get(CONF_MIN_ELEVATION, DEFAULT_MIN_ELEVATION))
    weather_entity = data.get(CONF_WEATHER_ENTITY, DEFAULT_WEATHER_ENTITY)

    entities = [
        SolarWindowSensor(
            hass=hass,
            entry=entry,
            window_name=w[CONF_WINDOW_NAME],
            facing=w[CONF_WINDOW_FACING],
            sun_cone=sun_cone,
            min_elevation=min_elevation,
            weather_entity=weather_entity,
        )
        for w in windows
    ]

    async_add_entities(entities, update_before_add=True)


class SolarWindowSensor(BinarySensorEntity):
    """Binary sensor that is ON when the sun is shining through a window."""

    _attr_device_class = BinarySensorDeviceClass.LIGHT
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        window_name: str,
        facing: str,
        sun_cone: float,
        min_elevation: float,
        weather_entity: str,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._window_name = window_name
        self._facing = facing
        self._facing_azimuth = FACING_AZIMUTHS.get(facing, 0)
        self._sun_cone = sun_cone
        self._min_elevation = min_elevation
        self._weather_entity = weather_entity

        self._attr_unique_id = f"{entry.entry_id}_{slugify(window_name)}"
        self._attr_name = f"{window_name} sunlit"
        self._attr_is_on = False

        self._sun_azimuth: float | None = None
        self._sun_elevation: float | None = None
        self._weather_state: str | None = None
        self._azimuth_diff: float | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Solar Windows",
            manufacturer="Solar Windows Integration",
            model="Sun position tracker",
            entry_type="service",
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_FACING: self._facing,
            ATTR_FACING_AZIMUTH: self._facing_azimuth,
            ATTR_SUN_AZIMUTH: self._sun_azimuth,
            ATTR_SUN_ELEVATION: self._sun_elevation,
            ATTR_AZIMUTH_DIFF: round(self._azimuth_diff, 1) if self._azimuth_diff is not None else None,
            ATTR_WEATHER_STATE: self._weather_state,
            ATTR_SUN_CONE: self._sun_cone,
        }

    @property
    def icon(self) -> str:
        return "mdi:weather-sunny" if self._attr_is_on else "mdi:weather-sunny-off"

    async def async_added_to_hass(self) -> None:
        """Register update interval when entity is added."""
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_update_callback,
                SCAN_INTERVAL,
            )
        )
        await self.async_update()

    @callback
    async def _async_update_callback(self, _now=None) -> None:
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Recalculate sunlit state from sun and weather entities."""
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is None:
            _LOGGER.warning("sun.sun entity not found — is the sun integration enabled?")
            self._attr_is_on = False
            return

        self._sun_azimuth = sun_state.attributes.get("azimuth")
        self._sun_elevation = sun_state.attributes.get("elevation")

        if self._sun_azimuth is None or self._sun_elevation is None:
            self._attr_is_on = False
            return

        # Calculate azimuth difference (shortest arc)
        diff = abs(self._sun_azimuth - self._facing_azimuth) % 360
        if diff > 180:
            diff = 360 - diff
        self._azimuth_diff = diff

        # Check weather if entity exists
        overcast = False
        weather_state_obj = self.hass.states.get(self._weather_entity)
        if weather_state_obj:
            self._weather_state = weather_state_obj.state
            overcast = self._weather_state in OVERCAST_STATES
        else:
            self._weather_state = None

        # Final determination
        self._attr_is_on = (
            self._sun_elevation > self._min_elevation
            and diff <= self._sun_cone
            and not overcast
        )
