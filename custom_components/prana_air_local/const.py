"""Constants for the AQI.in Monitor (local) integration."""
DOMAIN = "prana_air_local"

CONF_SCAN_SECONDS = "scan_seconds"
DEFAULT_SCAN_SECONDS = 60
MIN_SCAN_SECONDS = 30  # the monitor itself refreshes its page every 30 s
MAX_SCAN_SECONDS = 3600

MANUFACTURER = "AQI.in"
DEVICE_NAME = "AQI Monitor"
MODEL = "Air quality monitor"
