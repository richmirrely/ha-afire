"""Switch platform for AFIRE Fireplace."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import FLAG_POWER
from .entity import AfireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fireplace power."""
    async_add_entities([AfirePowerSwitch(entry.runtime_data.coordinator)])


class AfirePowerSwitch(AfireEntity, SwitchEntity):
    """Main fireplace power switch."""

    _attr_translation_key = "power"
    _attr_icon = "mdi:fireplace"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.enabled(FLAG_POWER)

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_execute(self.coordinator.client.async_set_power(True))

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_execute(self.coordinator.client.async_set_power(False))
