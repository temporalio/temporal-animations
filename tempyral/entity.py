from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Self

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

    def as_serializable(self) -> models.Entity:
        model = next(
            filter(
                None,
                (getattr(models, cls.__name__, None) for cls in self.__class__.mro()),
            )
        )
        data = {}
        for key in self.__publish__:
            val = getattr(self, key)
            if isinstance(val, Entity):
                data[key] = val.as_serializable()
            elif isinstance(val, Mapping):
                data[key] = {
                    k: v.as_serializable() if isinstance(v, Entity) else v
                    for k, v in val.items()
                }
            elif isinstance(val, str):
                data[key] = val
            elif isinstance(val, Iterable):
                data[key] = [
                    v.as_serializable() if isinstance(v, Entity) else v for v in val
                ]
            elif val.__class__.__name__ in ("WorkflowTask", "Activitytask"):
                data[key] = val.__dict__
            else:
                data[key] = val
        return model(**data)

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
