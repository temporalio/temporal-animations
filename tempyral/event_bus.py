from asyncio import Queue
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

E = TypeVar("E")


@dataclass
class StateChange(Generic[E]):
    entity: E


@dataclass
class Message(Generic[E]):
    sender: E
    receiver: E


class EventBus(Generic[E]):
    def __init__(self):
        self.bus: Queue[Union[StateChange[E], Message[E]]] = Queue()

    async def publish(self, event: Union[StateChange[E], Message[E]]):
        await self.bus.put(event)


event_bus = EventBus()
