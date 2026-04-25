from collections import namedtuple
from typing import List, Optional

from deps_message_flow.events.common import DomainEvent

__all__ = [
    "FakeDomainEventPublisher",
]

Events = namedtuple("Events", ("aggregate_type", "aggregate_id", "events"))


class FakeDomainEventPublisher:
    def __init__(self) -> None:
        self._last_published: Optional[Events] = None

    @property
    def last_published(self):
        return self._last_published

    @last_published.deleter
    def last_published(self):
        self._last_published = None

    def publish(
        self,
        aggregate_type: str,
        aggregate_id: str,
        domain_events: List[DomainEvent],
        **kwargs,
    ) -> None:
        self._last_published = Events(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            events=domain_events,
        )
