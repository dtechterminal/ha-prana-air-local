"""Home Assistant tests (pytest-homeassistant-custom-component)."""
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.prana_air_local.const import DOMAIN

pytest_plugins = ["pytest_homeassistant_custom_component"]

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
HOST = "esp32c3-E4F5"
DEVICE_ID = "a0b1c2d3e4f5"


def page(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def monitor(aioclient_mock):
    """The monitor answering at HOST and at 192.168.1.50."""
    for host in (HOST, "192.168.1.50"):
        aioclient_mock.get(f"http://{host}/data", text=page("data.html"))
        aioclient_mock.get(f"http://{host}/", text=page("root.html"))
    return aioclient_mock


@pytest.fixture
def entry(hass):
    e = MockConfigEntry(domain=DOMAIN, data={"host": HOST}, unique_id=DEVICE_ID,
                        title="AQI Monitor")
    e.add_to_hass(hass)
    return e
