"""Air quality, temperature and humidity sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription, SensorStateClass)
from homeassistant.const import (PERCENTAGE, UnitOfDensity, UnitOfRatio,
                                 UnitOfTemperature)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PranaAirConfigEntry
from .api import Reading
from .coordinator import PranaAirCoordinator
from .entity import PranaAirEntity


def _co2(reading: Reading) -> float | None:
    # Outdoor air is ~420 ppm, so 0 means "no reading" (warming up, or a
    # model without a CO2 cell), not clean air.
    return reading.co2 or None


@dataclass(frozen=True, kw_only=True)
class PranaAirSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Reading], float | None]


SENSORS: tuple[PranaAirSensorDescription, ...] = (
    PranaAirSensorDescription(
        key="pm25", device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.pm25),
    PranaAirSensorDescription(
        key="pm10", device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.pm10),
    PranaAirSensorDescription(
        key="pm1", device_class=SensorDeviceClass.PM1,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.pm1),
    PranaAirSensorDescription(
        key="co2", device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT, value_fn=_co2),
    PranaAirSensorDescription(
        key="temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.temperature),
    PranaAirSensorDescription(
        key="humidity", device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.humidity),
)


async def async_setup_entry(hass: HomeAssistant, entry: PranaAirConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PranaAirSensor(coordinator, d) for d in SENSORS)


class PranaAirSensor(PranaAirEntity, SensorEntity):
    entity_description: PranaAirSensorDescription

    def __init__(self, coordinator: PranaAirCoordinator,
                 description: PranaAirSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.coordinator.data)
