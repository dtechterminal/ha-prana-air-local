"""Diagnostics: the latest reading and how it was fetched."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any


async def async_get_config_entry_diagnostics(hass, entry) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": dict(entry.data),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "update_interval_seconds": coordinator.update_interval.total_seconds(),
        "reading": asdict(coordinator.data) if coordinator.data else None,
    }
