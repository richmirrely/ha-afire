"""Select platform for AFIRE Fireplace."""

from __future__ import annotations

from typing import ClassVar

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COLOR_KEYS,
    COLOR_OPTIONS,
    COLOR_OPTION_TO_KEY,
    FLAG_EFFECTS,
    FLAG_POWER,
    FLAG_RGB_POWER,
)
from .entity import AfireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fixed RGB colour preset selector."""
    async_add_entities([AfireRgbColorSelect(entry.runtime_data.coordinator)])


class AfireRgbColorSelect(AfireEntity, SelectEntity):
    """Choose one of the fireplace's 15 fixed RGB colour presets."""

    _attr_translation_key = "rgb_color"
    _attr_icon = "mdi:palette-swatch"
    _attr_options: ClassVar[list[str]] = list(COLOR_OPTIONS)

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "rgb_color")

    @property
    def current_option(self) -> str | None:
        """Return the colour preset currently reported by the fireplace."""
        bits = self.coordinator.data.bits
        for index, _key in enumerate(COLOR_KEYS):
            if bits & (1 << (index + 3)):
                return COLOR_OPTIONS[index]
        return None

    async def async_select_option(self, option: str) -> None:
        """Select an exact colour and leave animated-effect mode if needed."""
        client = self.coordinator.client
        state = self.coordinator.data

        if not state.enabled(FLAG_POWER):
            await client.async_set_power(True)
            state = await client.async_request_state()
        if not state.enabled(FLAG_RGB_POWER):
            await client.async_set_rgb_power(True)
            state = await client.async_request_state()
        if state.bits & FLAG_EFFECTS:
            await client.async_set_effect(None)
            await client.async_request_state()

        await self._async_execute(
            client.async_set_color(COLOR_OPTION_TO_KEY[option])
        )
