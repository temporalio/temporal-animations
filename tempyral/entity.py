from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, Self

from event_bus import MessageEvent, StateChangeEvent, event_bus
from logger import log


class Entity:
    """
    An entity in the simulation.

    It can publish two types of events to a renderer:
    - a change to its internal state
    - a message between two entities
    """

    next_id = defaultdict(int)
    terminate_simulation: Callable

    def __init__(self, time=0):
        key = type(self).__name__
        self.next_id[key] += 1
        self.id = self.next_id[key]
        self.time = time

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.id))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and hash(self) == hash(other)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    # A whitelist of instance attributes to be included in the object published
    # to the event bus.
    # TODO: publish serialized data to the event bus and make the schema
    # available to consumers (JSON, JSONSchema).
    __publish__ = {"id", "time"}

    def clone(self) -> Self:
        cloned = deepcopy(self)
        # Computed properties to be cloned must be named with a _ prefix.
        for k in self.__publish__ - self.__dict__.keys():
            setattr(cloned, k, deepcopy(getattr(self, "_" + k)))
        return cloned

    def __getstate__(self) -> dict:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k in self.__publish__ & self.__dict__.keys()
        }

    async def publish_change_event(self):
        log(f"{self}", "S: publish change")
        await event_bus.publish(StateChangeEvent(self.clone()))

    async def publish_message_event(
        self, sender: "Entity", receiver: "Entity", message: "Entity"
    ):
        log(f"{sender} -> {receiver}: {message}", "S: publish message")
        await event_bus.publish(
            MessageEvent(sender.clone(), receiver.clone(), message.clone())
        )
