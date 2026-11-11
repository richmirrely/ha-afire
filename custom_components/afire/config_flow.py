"""Config flow for AFIRE Fireplace."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import CONF_PASSCODE, DEFAULT_NAME, DOMAIN
from .gizwits import (
    AfireAuthenticationError,
    AfireClient,
    AfireConnectionError,
)


class AfireConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a local AFIRE fireplace."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            passcode = user_input[CONF_PASSCODE].strip()
            name = user_input[CONF_NAME].strip() or DEFAULT_NAME

            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            client = AfireClient(host, passcode)
            try:
                await client.async_request_state()
            except AfireAuthenticationError:
                errors["base"] = "invalid_auth"
            except AfireConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001  # pragma: no cover - HA flow guard
                errors["base"] = "unknown"
            finally:
                await client.async_disconnect()

            if not errors:
                return self.async_create_entry(
                    title=name,
                    data={CONF_HOST: host, CONF_PASSCODE: passcode},
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=(user_input or {}).get(CONF_HOST, ""),
                ): str,
                vol.Required(
                    CONF_PASSCODE,
                    default=(user_input or {}).get(CONF_PASSCODE, ""),
                ): str,
                vol.Optional(
                    CONF_NAME,
                    default=(user_input or {}).get(CONF_NAME, DEFAULT_NAME),
                ): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
