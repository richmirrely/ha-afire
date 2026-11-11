"""Number platform for AFIRE Fireplace."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import AfireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up flame level and speed controls."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            AfireLevelNumber(coordinator, "flame_level", "flame"),
            AfireLevelNumber(coordinator, "flame_speed", "speed"),
        ]
    )


class AfireLevelNumber(AfireEntity, NumberEntity):
    """Integer level from 1 to 8."""

    _attr_native_min_value = 1
    _attr_native_max_value = 8
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, key: str, state_attribute: str) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._state_attribute = state_attribute
        self._attr_icon = (
            "mdi:fire" if state_attribute == "flame" else "mdi:speedometer"
        )

    @property
    def native_value(self) -> int:
        return getattr(self.coordinator.data, self._state_attribute)

    async def async_set_native_value(self, value: float) -> None:
        level = int(value)
        if self._state_attribute == "flame":
            command = self.coordinator.client.async_set_flame(level)
        else:
            command = self.coordinator.client.async_set_speed(level)
        await self._async_execute(command)
