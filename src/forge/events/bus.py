"""Thread-safe event bus for publishing and subscribing to ForgeEvents."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Callable

from forge.events.models import ForgeEvent

logger = logging.getLogger("forge.events")

EventListener = Callable[[ForgeEvent], None]


class EventBus:
    """Thread-safe in-memory publish-subscribe event dispatcher."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[str, list[EventListener]] = defaultdict(list)
        self._wildcard_subscribers: list[EventListener] = []

    def subscribe(self, event_name: str, listener: EventListener) -> None:
        """Subscribe to a specific event by name, or use '*' for all events."""
        with self._lock:
            if event_name == "*":
                if listener not in self._wildcard_subscribers:
                    self._wildcard_subscribers.append(listener)
            else:
                if listener not in self._subscribers[event_name]:
                    self._subscribers[event_name].append(listener)

    def unsubscribe(self, event_name: str, listener: EventListener) -> None:
        """Unsubscribe a listener from an event."""
        with self._lock:
            if event_name == "*":
                if listener in self._wildcard_subscribers:
                    self._wildcard_subscribers.remove(listener)
            else:
                if listener in self._subscribers[event_name]:
                    self._subscribers[event_name].remove(listener)

    def publish(self, event: ForgeEvent) -> None:
        """Deliver an event to all matching subscribers safely."""
        with self._lock:
            listeners = list(self._subscribers.get(event.name, [])) + list(
                self._wildcard_subscribers
            )

        for listener in listeners:
            try:
                listener(event)
            except Exception as exc:
                logger.exception(
                    "Error dispatching event %s to listener %s: %s", event.name, listener, exc
                )


# Global singleton instance for system-wide lifecycle observation
_GLOBAL_BUS = EventBus()


def get_event_bus() -> EventBus:
    """Obtain the global event bus."""
    return _GLOBAL_BUS
