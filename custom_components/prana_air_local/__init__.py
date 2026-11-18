"""Prana Air air quality monitors, read over the local network."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import PranaAirCoordinator

PLATFORMS = [Platform.SENSOR]

type PranaAirConfigEntry = ConfigEntry[PranaAirCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PranaAirConfigEntry) -> bool:
    coordinator = PranaAirCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: PranaAirConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PranaAirConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
