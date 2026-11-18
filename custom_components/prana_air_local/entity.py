"""Shared device identity."""
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import format_mac
from .const import DEVICE_NAME, DOMAIN, MANUFACTURER, MODEL
from .coordinator import PranaAirCoordinator


class PranaAirEntity(CoordinatorEntity[PranaAirCoordinator]):
    # No name or translation key: the device class names each sensor
    # ("PM2.5", "Humidity", ...), translated by Home Assistant.
    _attr_has_entity_name = True

    def __init__(self, coordinator: PranaAirCoordinator, key: str) -> None:
        super().__init__(coordinator)
        device_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections={(CONNECTION_NETWORK_MAC, format_mac(device_id))},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"{coordinator.client.base_url}/data",
        )
