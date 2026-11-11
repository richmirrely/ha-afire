"""Data coordinator for the AFIRE Fireplace integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .gizwits import AfireClient, AfireError
from .protocol import AfireState

_LOGGER = logging.getLogger(__name__)


class AfireCoordinator(DataUpdateCoordinator[AfireState]):
    """Poll for recovery and accept push state reports while connected."""

    def __init__(
        self, hass: HomeAssistant, client: AfireClient, device_name: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=False,
        )
        self.client = client
        self.device_name = device_name
        self._remove_listener = client.add_state_listener(self._handle_push_state)

    async def _async_update_data(self) -> AfireState:
        try:
            return await self.client.async_request_state()
        except AfireError as err:
            raise UpdateFailed(str(err)) from err

    @callback
    def _handle_push_state(self, state: AfireState) -> None:
        self.async_set_updated_data(state)

    async def async_close(self) -> None:
        """Release the push subscription and TCP connection."""
        self._remove_listener()
        await self.client.async_disconnect()
