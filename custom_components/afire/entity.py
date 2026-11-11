"""Shared entity support for AFIRE Fireplace."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AfireCoordinator
from .gizwits import AfireError


class AfireEntity(CoordinatorEntity[AfireCoordinator]):
    """Base class for all entities belonging to the fireplace."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AfireCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.client.host)},
            name=coordinator.device_name,
            manufacturer="AFIRE Design",
            model="Fireplace (Gizwits GAgent)",
        )

    async def _async_execute(self, command: Awaitable[Any]) -> None:
        try:
            await command
            await self.coordinator.async_request_refresh()
        except AfireError as err:
            raise HomeAssistantError(str(err)) from err
