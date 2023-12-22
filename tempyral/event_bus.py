from asyncio import Queue
from dataclasses import dataclass
from typing import Any, Dict, Union

from tempyral.simulation import Entity


@dataclass
class StateChangeEvent:
    entity: Entity


@dataclass
class MessageEvent:
    sender: Entity
    receiver: Entity
    data: Dict[str, Any]


class EventBus:
    def __init__(self):
        self.bus: Queue[Union[StateChangeEvent, MessageEvent]] = Queue()

    async def publish(self, event: Union[StateChangeEvent, MessageEvent]):
        await self.bus.put(event)


event_bus = EventBus()
