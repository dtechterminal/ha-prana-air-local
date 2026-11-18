from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfDensity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.prana_air_local.const import DOMAIN

from .conftest import DEVICE_ID, HOST, page

UG = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER

EXPECTED = {
    "sensor.aqi_monitor_pm2_5": ("124", UG),
    "sensor.aqi_monitor_pm10": ("144", UG),
    "sensor.aqi_monitor_pm1": ("78", UG),
    "sensor.aqi_monitor_temperature": ("27", "°C"),
    "sensor.aqi_monitor_humidity": ("41", "%"),
}


async def test_sensors(hass, monitor, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for entity_id, (value, unit) in EXPECTED.items():
        state = hass.states.get(entity_id)
        assert state, entity_id
        assert state.state == value, entity_id
        assert state.attributes["unit_of_measurement"] == unit
        assert state.attributes["state_class"] == "measurement"
    # CO2 0 ppm is "no reading", not clean air.
    assert hass.states.get("sensor.aqi_monitor_carbon_dioxide").state == STATE_UNKNOWN

    ent = er.async_get(hass).async_get("sensor.aqi_monitor_pm2_5")
    assert ent.unique_id == f"{DEVICE_ID}_pm25"
    device = dr.async_get(hass).async_get(ent.device_id)
    assert (dr.CONNECTION_NETWORK_MAC, "a0:b1:c2:d3:e4:f5") in device.connections
    assert device.identifiers == {(DOMAIN, DEVICE_ID)}
    assert device.configuration_url == f"http://{HOST}/data"
    assert (device.manufacturer, device.name) == ("AQI.in", "AQI Monitor")


async def test_goes_unavailable_and_recovers(hass, monitor, entry, aioclient_mock):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{HOST}/data", exc=aiohttp.ClientError("gone"))
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.aqi_monitor_pm2_5").state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"http://{HOST}/data",
                       text=page("data.html").replace(">124<", ">35<"))
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=122))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.aqi_monitor_pm2_5").state == "35"


async def test_setup_retries_when_offline(hass, aioclient_mock, entry):
    aioclient_mock.get(f"http://{HOST}/data", exc=aiohttp.ClientError("down"))
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload(hass, monitor, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_diagnostics(hass, monitor, entry):
    from custom_components.prana_air_local.diagnostics import (
        async_get_config_entry_diagnostics)
    assert await hass.config_entries.async_setup(entry.entry_id)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["reading"]["pm25"] == 124
    assert diag["entry"] == {"host": HOST}
