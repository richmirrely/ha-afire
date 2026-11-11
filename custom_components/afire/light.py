"""Light platform for AFIRE Fireplace."""

from __future__ import annotations

from math import inf
from typing import Any, ClassVar

from homeassistant.components.light import (
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    EFFECT_OFF,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COLOR_KEYS,
    COLOR_RGB,
    EFFECT_FADE1,
    EFFECT_FADE2,
    EFFECT_SMOOTH,
    EFFECTS,
    FLAG_EFFECTS,
    FLAG_FADE1,
    FLAG_FADE2,
    FLAG_ORANGE_LIGHT,
    FLAG_POWER,
    FLAG_RGB_POWER,
    FLAG_SMOOTH,
)
from .entity import AfireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up orange and RGB lights."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([AfireOrangeLight(coordinator), AfireRgbLight(coordinator)])


class AfireOrangeLight(AfireEntity, LightEntity):
    """Binary orange decorative light."""

    _attr_translation_key = "orange_light"
    _attr_icon = "mdi:lightbulb"
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "orange_light")

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data
        return state.enabled(FLAG_POWER) and state.enabled(FLAG_ORANGE_LIGHT)

    async def async_turn_on(self, **kwargs: Any) -> None:
        client = self.coordinator.client
        if not self.coordinator.data.enabled(FLAG_POWER):
            await client.async_set_power(True)
            await client.async_request_state()
        await self._async_execute(client.async_set_orange_light(True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_execute(self.coordinator.client.async_set_orange_light(False))


class AfireRgbLight(AfireEntity, LightEntity):
    """RGB light backed by 15 fixed presets and three effects."""

    _attr_translation_key = "rgb_light"
    _attr_icon = "mdi:palette"
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list: ClassVar[list[str]] = list(EFFECTS)

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "rgb_light")

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data
        return state.enabled(FLAG_POWER) and state.enabled(FLAG_RGB_POWER)

    @property
    def color_mode(self) -> ColorMode:
        return ColorMode.RGB

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        bits = self.coordinator.data.bits
        for index, key in enumerate(COLOR_KEYS):
            if bits & (1 << (index + 3)):
                return COLOR_RGB[key]
        return None

    @property
    def effect(self) -> str:
        bits = self.coordinator.data.bits
        if bits & FLAG_SMOOTH:
            return EFFECT_SMOOTH
        if bits & FLAG_FADE1:
            return EFFECT_FADE1
        if bits & FLAG_FADE2:
            return EFFECT_FADE2
        return EFFECT_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        client = self.coordinator.client
        state = self.coordinator.data

        if not state.enabled(FLAG_POWER):
            await client.async_set_power(True)
            state = await client.async_request_state()
        if not state.enabled(FLAG_RGB_POWER):
            await client.async_set_rgb_power(True)
            await client.async_request_state()

        if ATTR_EFFECT in kwargs:
            requested_effect = kwargs[ATTR_EFFECT]
            await client.async_set_effect(
                None if requested_effect == EFFECT_OFF else requested_effect
            )
        elif rgb := kwargs.get(ATTR_RGB_COLOR):
            if self.coordinator.data.bits & FLAG_EFFECTS:
                await client.async_set_effect(None)
                await client.async_request_state()
            await client.async_set_color(_nearest_color_key(rgb))

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_execute(self.coordinator.client.async_set_rgb_power(False))


def _nearest_color_key(rgb: tuple[int, int, int]) -> str:
    """Return the AFIRE preset nearest to the requested RGB colour."""
    nearest = COLOR_KEYS[0]
    nearest_distance = inf
    for key, candidate in COLOR_RGB.items():
        distance = sum(
            (requested - actual) ** 2 for requested, actual in zip(rgb, candidate)
        )
        if distance < nearest_distance:
            nearest = key
            nearest_distance = distance
    return nearest
