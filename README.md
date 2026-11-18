# AQI.in Monitor (Local) for Home Assistant

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/prana_air_local/brand/dark_logo@2x.png">
  <img src="custom_components/prana_air_local/brand/logo@2x.png" alt="AQI.in" width="160">
</picture>

Reads an [AQI.in](https://www.aqi.in/) air quality monitor over your local
network, with no cloud account. The monitor's ESP32 runs Prana Air firmware
(its pages say "Bohu Monitor" and "By Prana Air") and serves its live readings
as a web page at `http://<monitor>/data`. This integration polls that page.

## Sensors

| Sensor | Unit | Notes |
|---|---|---|
| PM2.5 | µg/m³ | |
| PM10 | µg/m³ | |
| PM1 | µg/m³ | |
| Carbon dioxide | ppm | The monitor shows 0 when it has no CO₂ reading (warming up, or a model without a CO₂ cell). That is reported as *unknown*, not 0 |
| Temperature | °C | Whole degrees, as the monitor shows them |
| Humidity | % | |

All sensors have state class *measurement*, so they get long-term statistics.
They go unavailable when the monitor stops answering and recover by themselves.

## Installation

1. In Home Assistant, open **HACS**, search for **AQI.in Monitor (Local)** and download it.
2. Restart Home Assistant.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dtechterminal&repository=ha-prana-air-local&category=integration)

Without HACS: copy `custom_components/prana_air_local` into your
`config/custom_components/` folder and restart Home Assistant.

## Setup

**Settings → Devices & services → Add integration → AQI.in Monitor (Local)**, then
enter the monitor's IP address or DHCP host name (it shows up as
`esp32c3-XXXXXX`, where `XXXXXX` is the end of its MAC address).

- The monitor's IP address can change when its DHCP lease renews. A host name or a
  DHCP reservation avoids that. If you set it up by IP address, Home Assistant
  follows the monitor to its new address when it sees it on DHCP.
- Home Assistant may also discover the monitor on DHCP and offer to add it. The
  match is any `esp32c3-*` host, so each candidate is checked for the readings
  page before anything is offered.
- **Reconfigure** on the integration entry changes the address.
- **Configure** sets the poll interval (default 60 s, minimum 30 s; the monitor
  refreshes its page every 30 s).

The device ID is the monitor's MAC address, read from its Wi-Fi setup page at `/`.

## Security note

The monitor has no authentication. Anyone on the same network can open its
Wi-Fi setup page at `/` and move it to another network. Keep it on a network
segment that only Home Assistant needs to reach, if you can. The integration
only sends GET requests to `/data` and `/`.

## Development

```sh
uv venv -p 3.14 .venv
uv pip install -p .venv/bin/python pytest-homeassistant-custom-component ruff
.venv/bin/ruff check custom_components tests tests_ha
.venv/bin/pytest -q tests        # page parser
.venv/bin/pytest -q tests_ha     # config flow and sensors in Home Assistant
```

`tests/fixtures/` holds pages captured from a monitor (the device ID and Wi-Fi
network list are replaced). Brand images: see [docs/branding.md](docs/branding.md).

AQI.in and Prana Air names and logos belong to their owners. This is an
independent community integration, not made or endorsed by AQI.in or Prana Air.
