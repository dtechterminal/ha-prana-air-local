from pathlib import Path

import pytest

from prana_lib.api import (PranaAirClient, PranaAirParseError, Reading, format_mac,
                           parse_data_page, parse_device_id)

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_parses_live_page():
    assert parse_data_page(fixture("data.html")) == Reading(
        pm25=124, pm10=144, pm1=78, co2=0, temperature=27, humidity=41)


def test_parses_decimals_and_negative_temperature():
    page = fixture("data.html").replace("Temp:27", "Temp:-3.5").replace(">124<", ">7<")
    reading = parse_data_page(page)
    assert reading.temperature == -3.5
    assert reading.pm25 == 7


def test_missing_optional_values_are_none():
    page = ("<html><head><title>Bohu Monitor</title></head><body>"
            "<label >PM2.5 </label><label >12</label></body></html>")
    assert parse_data_page(page) == Reading(pm25=12)


@pytest.mark.parametrize("name", ["root.html", "status.html"])
def test_other_pages_are_rejected(name):
    with pytest.raises(PranaAirParseError):
        parse_data_page(fixture(name))


def test_foreign_page_is_rejected():
    with pytest.raises(PranaAirParseError):
        parse_data_page("<html><head><title>Router</title></head>"
                        "<body><label>PM2.5</label><label>5</label></body></html>")


def test_device_id():
    assert parse_device_id(fixture("root.html")) == "a0b1c2d3e4f5"
    assert parse_device_id(fixture("data.html")) is None
    assert format_mac("a0b1c2d3e4f5") == "a0:b1:c2:d3:e4:f5"


@pytest.mark.parametrize("host", ["esp32c3-ABC", "http://esp32c3-ABC/", " esp32c3-ABC "])
def test_host_normalised(host):
    assert PranaAirClient(None, host).base_url == "http://esp32c3-ABC"
