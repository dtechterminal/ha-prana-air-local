"""Local HTTP client for AQI.in air quality monitors.

The monitors run Prana Air firmware (page titles "Bohu Monitor" / "Prana Air").

The monitor's ESP32 serves two HTML pages and no JSON:

* ``/data``: the live readings (PM2.5, PM1, PM10, CO2, temperature, humidity),
  each inside a ``<label>``. The page reloads itself every 30 seconds.
* ``/``: the Wi-Fi setup form, which also shows the device ID (its MAC address).

The pages carry no authentication, so this client only ever sends GET requests.
"""
from __future__ import annotations

import asyncio
import html
import re
from dataclasses import dataclass

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=10)

_LABEL_RE = re.compile(r"<label[^>]*>(.*?)</label>", re.IGNORECASE | re.DOTALL)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_ID_RE = re.compile(r"\bID:\s*([0-9A-Fa-f]{12})\b")
_NUMBER = r"(-?\d+(?:\.\d+)?)"
_PAIR_RE = {
    "pm1": re.compile(rf"^PM1\s*:\s*{_NUMBER}$", re.IGNORECASE),
    "pm10": re.compile(rf"^PM10\s*:\s*{_NUMBER}$", re.IGNORECASE),
    "temperature": re.compile(rf"^Temp\s*:\s*{_NUMBER}$", re.IGNORECASE),
    "humidity": re.compile(rf"^Humi\s*:\s*{_NUMBER}$", re.IGNORECASE),
}
# Headline values sit in the label right after their caption.
_HEADLINE = {"pm2.5": "pm25", "co2": "co2"}
_KNOWN_TITLES = ("bohu monitor", "prana air")


class PranaAirError(Exception):
    """The monitor could not be reached."""


class PranaAirParseError(PranaAirError):
    """The page was not an AQI.in monitor (Prana Air firmware) readings page."""


@dataclass(frozen=True)
class Reading:
    pm25: float | None = None
    pm10: float | None = None
    pm1: float | None = None
    co2: float | None = None
    temperature: float | None = None
    humidity: float | None = None


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return int(value) if value.is_integer() else value


def _labels(page: str) -> list[str]:
    return [" ".join(html.unescape(re.sub(r"<[^>]+>", "", m)).split())
            for m in _LABEL_RE.findall(page)]


def parse_data_page(page: str) -> Reading:
    """Read the values from the ``/data`` page."""
    title = _TITLE_RE.search(page)
    if title and not any(t in title.group(1).lower() for t in _KNOWN_TITLES):
        raise PranaAirParseError(f"unexpected page title {title.group(1).strip()!r}")
    labels = _labels(page)
    values: dict[str, float | None] = {}
    for i, label in enumerate(labels):
        key = _HEADLINE.get(label.lower())
        if key and i + 1 < len(labels):
            values[key] = _number(labels[i + 1])
            continue
        for name, pattern in _PAIR_RE.items():
            if match := pattern.match(label):
                values[name] = _number(match.group(1))
    if values.get("pm25") is None:
        raise PranaAirParseError("no PM2.5 value on the page")
    return Reading(**values)


def parse_device_id(page: str) -> str | None:
    """Return the device ID (MAC, lower-case hex, no separators) from ``/``."""
    match = _ID_RE.search(page)
    return match.group(1).lower() if match else None


def format_mac(device_id: str) -> str:
    return ":".join(device_id[i:i + 2] for i in range(0, 12, 2))


class PranaAirClient:
    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self.host = host.strip().rstrip("/")
        if self.host.startswith(("http://", "https://")):
            self.host = self.host.split("://", 1)[1]

    @property
    def base_url(self) -> str:
        return f"http://{self.host}"

    async def _get(self, path: str) -> str:
        try:
            async with self._session.get(f"{self.base_url}{path}", timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                # The firmware sends no charset; the pages are plain ASCII.
                return await resp.text(encoding="utf-8", errors="replace")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PranaAirError(f"{self.base_url}{path}: {err!r}") from err

    async def read(self) -> Reading:
        return parse_data_page(await self._get("/data"))

    async def device_id(self) -> str | None:
        return parse_device_id(await self._get("/"))
