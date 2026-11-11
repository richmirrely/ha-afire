"""AFIRE Fireplace integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_PASSCODE, PLATFORMS
from .coordinator import AfireCoordinator
from .gizwits import AfireClient


@dataclass(slots=True)
class AfireRuntimeData:
    """Objects owned by one AFIRE config entry."""

    client: AfireClient
    coordinator: AfireCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AFIRE from a config entry."""
    client = AfireClient(entry.data[CONF_HOST], entry.data[CONF_PASSCODE])
    coordinator = AfireCoordinator(hass, client, entry.title)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = AfireRuntimeData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an AFIRE config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.coordinator.async_close()
    return unload_ok
