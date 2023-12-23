from asyncio import Queue
from dataclasses import dataclass
from typing import Any, Dict, Generic, TypeVar, Union

E = TypeVar("E")


@dataclass
class StateChangeEvent(Generic[E]):
    entity: E
    data: Dict[str, Any]


@dataclass
class MessageEvent(Generic[E]):
    sender: E
    receiver: E
    data: Dict[str, Any]


class TerminateSimulation:
    pass


class EventBus(Generic[E]):
    def __init__(self):
        self.bus: Queue[
            Union[StateChangeEvent[E], MessageEvent[E], TerminateSimulation]
        ] = Queue()

    async def publish(
        self, event: Union[StateChangeEvent[E], MessageEvent[E], TerminateSimulation]
    ):
        await self.bus.put(event)


event_bus = EventBus()
