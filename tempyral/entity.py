from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING, Callable, Self, Type, cast

from common.event_bus import (
    event_bus,
    get_serializable_data,
    make_message_event,
    make_state_change_event,
)
from common.logger import log
from schema import schema

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

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    __publish__ = {"id", "time"}

    @classmethod
    def get_serializable_cls(cls) -> Type[schema.Entity]:
        model = next(
            filter(
                None,
                (
                    getattr(schema, parent_cls.__name__, None)
                    for parent_cls in cls.mro()
                ),
            )
        )
        return model

    def as_serializable(self) -> schema.Entity:
        cls = self.get_serializable_cls()
        data = cast(dict, get_serializable_data(self))
        obj = cls(**data)
        print(f"{self.__class__.__name__}[{self.id}] => {cls.__name__}[{obj.id}]")
        return obj

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
