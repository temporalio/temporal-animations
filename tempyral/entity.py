from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Self, Type

from common.event_bus import event_bus, make_message_event, make_state_change_event
from common.logger import log
from schema import models

if TYPE_CHECKING:
    from tempyral.request_response import RequestResponse, Response


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

    __publish__ = {"id", "time"}

    @classmethod
    def get_serializable_cls(cls) -> Type[models.Entity]:
        return next(
            filter(
                None,
                (
                    getattr(models, parent_cls.__name__, None)
                    for parent_cls in cls.mro()
                ),
            )
        )

    def get_serializable_data(self) -> dict[str, Any]:
        return {
            k: v.value if isinstance(v, Enum) else v
            for k in self.__publish__
            for v in [getattr(self, k)]
        }

    def as_serializable(self) -> models.Entity:
        return self.get_serializable_cls()(**self.get_serializable_data())

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
        await event_bus.publish(make_state_change_event(self.clone()))

    async def publish_message_event(
        self,
        sender: "Entity",
        receiver: "Entity",
        message: "RequestResponse | Response",
    ):
        log(f"{message.id}: {sender} -> {receiver}: {message}", "S: publish message")
        await event_bus.publish(
            make_message_event(sender.clone(), receiver.clone(), message.clone())
        )

    def tick(self, message: "Entity"):
        message.time = self.time = max(self.time, message.time) + 1
