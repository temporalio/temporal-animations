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


class EventBus(Generic[E]):
    def __init__(self):
        self.bus: Queue[Union[StateChangeEvent[E], MessageEvent[E]]] = Queue()

    async def publish(self, event: Union[StateChangeEvent[E], MessageEvent[E]]):
        await self.bus.put(event)

    def empty(self) -> bool:
        return self.bus.empty()


event_bus = EventBus()
