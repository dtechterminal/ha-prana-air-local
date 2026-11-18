import aiohttp
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from custom_components.prana_air_local.const import CONF_SCAN_SECONDS, DOMAIN

from .conftest import DEVICE_ID, HOST, page

DHCP = DhcpServiceInfo(ip="192.168.1.50", hostname="esp32c3-e4f5",
                       macaddress="a0b1c2d3e4f5")


async def _user(hass, host):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})
    return await hass.config_entries.flow.async_configure(result["flow_id"], {"host": host})


async def test_user_flow(hass, monitor):
    result = await _user(hass, HOST)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": HOST}
    assert result["result"].unique_id == DEVICE_ID


async def test_user_flow_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get("http://nowhere/data", exc=aiohttp.ClientError("down"))
    result = await _user(hass, "nowhere")
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_not_prana(hass, aioclient_mock):
    aioclient_mock.get("http://router/data", text="<html><title>Router</title></html>")
    result = await _user(hass, "router")
    assert result["errors"] == {"base": "not_prana_air"}


async def test_user_flow_no_device_id(hass, aioclient_mock):
    aioclient_mock.get("http://odd/data", text=page("data.html"))
    aioclient_mock.get("http://odd/", text="<html></html>")
    result = await _user(hass, "odd")
    assert result["errors"] == {"base": "no_device_id"}


async def test_user_flow_duplicate_updates_host(hass, monitor, entry):
    result = await _user(hass, "192.168.1.50")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.168.1.50"


async def test_dhcp_discovery(hass, monitor):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP)
    assert result["step_id"] == "discovery_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": "192.168.1.50"}


async def test_dhcp_other_esp32_aborts(hass, aioclient_mock):
    aioclient_mock.get("http://192.168.1.50/data", status=404)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_dhcp_follows_ip_entry(hass, aioclient_mock):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    e = MockConfigEntry(domain=DOMAIN, data={"host": "192.168.1.9"}, unique_id=DEVICE_ID)
    e.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP)
    assert result["reason"] == "already_configured"
    assert e.data["host"] == "192.168.1.50"


async def test_dhcp_keeps_hostname_entry(hass, entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP)
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == HOST


async def test_reconfigure(hass, monitor, entry):
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.168.1.50"})
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.168.1.50"


async def test_reconfigure_wrong_device(hass, monitor, entry, aioclient_mock):
    aioclient_mock.get("http://other/data", text=page("data.html"))
    aioclient_mock.get("http://other/", text=page("root.html").replace("A0B1C2D3E4F5",
                                                                       "FFFFFFFFFFFF"))
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"],
                                                            {"host": "other"})
    assert result["reason"] == "wrong_device"
    assert entry.data["host"] == HOST


async def test_options(hass, monitor, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_SECONDS: 120})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval.total_seconds() == 120
