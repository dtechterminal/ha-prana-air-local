"""Set up a monitor by host name or IP, or from DHCP discovery."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (ConfigEntry, ConfigFlow, ConfigFlowResult,
                                          OptionsFlow)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.selector import (NumberSelector, NumberSelectorConfig,
                                            NumberSelectorMode)
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.util.network import is_ip_address

from .api import PranaAirClient, PranaAirError, PranaAirParseError
from .const import (CONF_SCAN_SECONDS, DEFAULT_SCAN_SECONDS, DOMAIN, MAX_SCAN_SECONDS,
                    MIN_SCAN_SECONDS)

_LOGGER = logging.getLogger(__name__)


class PranaAirConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None

    async def _probe(self, host: str) -> tuple[str | None, str | None]:
        """Return (device_id, error_key) for the monitor at host."""
        client = PranaAirClient(async_get_clientsession(self.hass), host)
        try:
            await client.read()
            device_id = await client.device_id()
        except PranaAirParseError:
            return None, "not_prana_air"
        except PranaAirError as err:
            _LOGGER.debug("Probe of %s failed: %s", host, err)
            return None, "cannot_connect"
        if not device_id:
            return None, "no_device_id"
        return device_id, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None
                              ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            device_id, error = await self._probe(host)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(title="Prana Air", data={CONF_HOST: host})
        return self.async_show_form(
            step_id="user", errors=errors,
            data_schema=vol.Schema({vol.Required(
                CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str}))

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        device_id = format_mac(discovery_info.macaddress).replace(":", "")
        await self.async_set_unique_id(device_id)
        # A known monitor that moved to a new address: follow it, unless it was
        # set up by host name, which keeps resolving to the right address.
        entry = self.hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, device_id)
        if entry and not is_ip_address(entry.data[CONF_HOST]):
            return self.async_abort(reason="already_configured")
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        # The DHCP match is broad (any ESP32-C3), so check it really is a monitor.
        probed_id, error = await self._probe(discovery_info.ip)
        if error or probed_id != device_id:
            return self.async_abort(reason=error or "not_prana_air")
        self._host = discovery_info.ip
        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None
                                           ) -> ConfigFlowResult:
        assert self._host
        if user_input is not None:
            return self.async_create_entry(title="Prana Air", data={CONF_HOST: self._host})
        self._set_confirm_only()
        return self.async_show_form(step_id="discovery_confirm",
                                    description_placeholders={"host": self._host})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None
                                     ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            device_id, error = await self._probe(host)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(entry, data={CONF_HOST: host})
        return self.async_show_form(
            step_id="reconfigure", errors=errors,
            data_schema=vol.Schema({vol.Required(CONF_HOST,
                                                 default=entry.data[CONF_HOST]): str}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PranaAirOptionsFlow()


class PranaAirOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None
                              ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_SECONDS: int(user_input[CONF_SCAN_SECONDS])})
        current = self.config_entry.options.get(CONF_SCAN_SECONDS, DEFAULT_SCAN_SECONDS)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required(CONF_SCAN_SECONDS, default=current): NumberSelector(
                NumberSelectorConfig(min=MIN_SCAN_SECONDS, max=MAX_SCAN_SECONDS, step=10,
                                     unit_of_measurement="s",
                                     mode=NumberSelectorMode.BOX)),
        }))
