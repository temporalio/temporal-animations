import asyncio
from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, Hashable, Self

from event_bus import MessageEvent, StateChangeEvent, event_bus
from log import log


class Entity:
    """
    An entity in the simulation.

    It can publish two types of events to a renderer:
    - a change to its internal state
    - a message between two entities
    """

    next_id = defaultdict(int)
    terminate_simulation: Callable

    def __init__(self):
        key = type(self).__name__
        self.next_id[key] += 1
        self.id = self.next_id[key]

    def __hash__(self) -> int:
        # Cloned instances have the same hash value. The cloned instances are
        # published to the event bus; sharing hash values like this allows event
        # bus consumers to track entity identities across different events.
        return hash((type(self).__name__, self.id))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and hash(self) == hash(other)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    __publish__ = ["id"]

    def publish(self) -> Self:
        return deepcopy(self)

    def __getstate__(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k in self.__publish__}

    async def publish_change_event(self):
        log(f"{self}", "S: publish change")
        await event_bus.publish(StateChangeEvent(self.publish()))
        await asyncio.sleep(0)

    async def publish_message_event(
        self, sender: "Entity", receiver: "Entity", **kwargs: Hashable
    ):
        log(f"{sender} -> {receiver}, {kwargs}", "S: publish message")
        await event_bus.publish(
            MessageEvent(sender.publish(), receiver.publish(), kwargs)
        )
        await asyncio.sleep(0)
