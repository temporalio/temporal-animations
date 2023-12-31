from asyncio import Queue
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

E = TypeVar("E")


@dataclass
class StateChangeEvent(Generic[E]):
    entity: E


@dataclass
class MessageEvent(Generic[E]):
    sender: E
    receiver: E
    entity: E


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
