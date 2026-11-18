"""Polls the monitor's /data page."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PranaAirClient, PranaAirError, Reading
from .const import CONF_SCAN_SECONDS, DEFAULT_SCAN_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PranaAirCoordinator(DataUpdateCoordinator[Reading]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        seconds = entry.options.get(CONF_SCAN_SECONDS, DEFAULT_SCAN_SECONDS)
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=timedelta(seconds=seconds))
        self.client = PranaAirClient(async_get_clientsession(hass), entry.data[CONF_HOST])

    async def _async_update_data(self) -> Reading:
        try:
            return await self.client.read()
        except PranaAirError as err:
            raise UpdateFailed(str(err)) from err
