"""Config flow for Solar Windows integration."""
from __future__ import annotations

import json
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    FACING_DIRECTIONS,
)

_LOGGER = logging.getLogger(__name__)


class SolarWindowsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Solar Windows."""

    VERSION = 1

    def __init__(self):
        self._windows: list[dict] = []

    async def async_step_user(self, user_input=None):
        """Step 1: Global settings (weather entity, cone angle, min elevation)."""
        errors = {}

        if user_input is not None:
            self._global = user_input
            return await self.async_step_add_window()

        schema = vol.Schema({
            vol.Optional(CONF_WEATHER_ENTITY, default=DEFAULT_WEATHER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="weather")
            ),
            vol.Optional(CONF_SUN_CONE, default=DEFAULT_SUN_CONE): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=90, step=5, mode="slider")
            ),
            vol.Optional(CONF_MIN_ELEVATION, default=DEFAULT_MIN_ELEVATION): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=20, step=1, mode="slider")
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={
                "info": "Configure global sun detection settings. You can add windows in the next step."
            },
            errors=errors,
        )

    async def async_step_add_window(self, user_input=None):
        """Step 2: Add a window."""
        errors = {}

        if user_input is not None:
            if user_input.get("action") == "done":
                if not self._windows:
                    errors["base"] = "no_windows"
                else:
                    return self._create_entry()
            else:
                name = user_input.get(CONF_WINDOW_NAME, "").strip()
                facing = user_input.get(CONF_WINDOW_FACING)
                if not name:
                    errors[CONF_WINDOW_NAME] = "invalid_name"
                elif facing not in FACING_DIRECTIONS:
                    errors[CONF_WINDOW_FACING] = "invalid_facing"
                else:
                    self._windows.append({
                        CONF_WINDOW_NAME: name,
                        CONF_WINDOW_FACING: facing,
                    })
                    if user_input.get("add_another"):
                        pass
                    else:
                        return self._create_entry()

        window_count = len(self._windows)
        description = (
            f"Windows added so far: {window_count}. "
            "Add another window or click 'Finish' to complete setup."
            if window_count > 0
            else "Add your first window. You can add more after."
        )

        schema = vol.Schema({
            vol.Required(CONF_WINDOW_NAME): selector.TextSelector(),
            vol.Required(CONF_WINDOW_FACING): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=FACING_DIRECTIONS,
                    mode="dropdown",
                )
            ),
            vol.Optional("add_another", default=True): selector.BooleanSelector(),
        })

        return self.async_show_form(
            step_id="add_window",
            data_schema=schema,
            description_placeholders={"description": description, "count": str(window_count)},
            errors=errors,
            last_step=False,
        )

    def _create_entry(self):
        """Create the config entry with all collected data."""
        return self.async_create_entry(
            title=f"Solar Windows ({len(self._windows)} window{'s' if len(self._windows) != 1 else ''})",
            data={
                **self._global,
                CONF_WINDOWS: self._windows,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarWindowsOptionsFlow(config_entry)


class SolarWindowsOptionsFlow(config_entries.OptionsFlow):
    """Handle options (edit windows after setup)."""

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._windows: list[dict] = list(config_entry.data.get(CONF_WINDOWS, []))

    async def async_step_init(self, user_input=None):
        """Show current windows as JSON for editing, plus global settings."""
        errors = {}

        if user_input is not None:
            try:
                windows_raw = user_input.get("windows_json", "[]")
                windows = json.loads(windows_raw)
                if not isinstance(windows, list):
                    raise ValueError
                for w in windows:
                    if CONF_WINDOW_NAME not in w or CONF_WINDOW_FACING not in w:
                        raise ValueError
                    if w[CONF_WINDOW_FACING] not in FACING_DIRECTIONS:
                        raise ValueError

                new_data = dict(self._config_entry.data)
                new_data[CONF_WINDOWS] = windows
                new_data[CONF_WEATHER_ENTITY] = user_input.get(CONF_WEATHER_ENTITY, DEFAULT_WEATHER_ENTITY)
                new_data[CONF_SUN_CONE] = user_input.get(CONF_SUN_CONE, DEFAULT_SUN_CONE)
                new_data[CONF_MIN_ELEVATION] = user_input.get(CONF_MIN_ELEVATION, DEFAULT_MIN_ELEVATION)

                self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
                return self.async_create_entry(title="", data={})

            except (json.JSONDecodeError, ValueError, KeyError):
                errors["windows_json"] = "invalid_windows_json"

        current_windows = self._config_entry.data.get(CONF_WINDOWS, [])
        current_json = json.dumps(current_windows, indent=2)

        schema = vol.Schema({
            vol.Optional(
                CONF_WEATHER_ENTITY,
                default=self._config_entry.data.get(CONF_WEATHER_ENTITY, DEFAULT_WEATHER_ENTITY)
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
            vol.Optional(
                CONF_SUN_CONE,
                default=self._config_entry.data.get(CONF_SUN_CONE, DEFAULT_SUN_CONE)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=90, step=5, mode="slider")
            ),
            vol.Optional(
                CONF_MIN_ELEVATION,
                default=self._config_entry.data.get(CONF_MIN_ELEVATION, DEFAULT_MIN_ELEVATION)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=20, step=1, mode="slider")
            ),
            vol.Optional("windows_json", default=current_json): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "info": 'Edit windows as JSON. Each entry needs "name" and "facing" (N/NE/E/SE/S/SW/W/NW).'
            },
            errors=errors,
        )
