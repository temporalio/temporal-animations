import asyncio
from collections import defaultdict
from copy import deepcopy
from typing import Any, Self

from tempyral.event_bus import MessageEvent, StateChangeEvent, event_bus


class Entity:
    next_id = defaultdict(int)

    def __init__(self):
        key = type(self).__name__
        self.next_id[key] += 1
        self.id = self.next_id[key]

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.id))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and hash(self) == hash(other)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    def clone(self) -> Self:
        return deepcopy(self)

    async def publish_change_event(self, **kwargs):
        await event_bus.publish(StateChangeEvent(self.clone(), kwargs))
        await asyncio.sleep(0)

    async def publish_message_event(
        self, sender: "Entity", receiver: "Entity", **kwargs
    ):
        if event_bus is not None:
            await event_bus.publish(
                MessageEvent(sender.clone(), receiver.clone(), kwargs)
            )
            await asyncio.sleep(0)
