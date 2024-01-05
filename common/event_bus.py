from asyncio import Queue
from enum import Enum
from types import NoneType
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from schema import schema

if TYPE_CHECKING:
    import tempyral


def get_serializable_data(obj: Any) -> dict | list | int | bool | str | None:
    if hasattr(obj, "__publish__"):
        return {k: get_serializable_data(getattr(obj, k)) for k in obj.__publish__}
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, Mapping):
        return {k: get_serializable_data(v) for k, v in obj.items()}
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, Iterable):
        return [get_serializable_data(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        return get_serializable_data(obj.__dict__)
    elif isinstance(obj, (int, bool, NoneType)):
        return obj
    else:
        raise TypeError(f"Unexpected type: {type(obj)}")


def make_state_change_event(
    entity: "tempyral.Entity",
) -> schema.StateChangeEvent:
    return schema.StateChangeEvent(entity=entity.as_serializable())


def make_message_event(
    sender: "tempyral.Entity",
    receiver: "tempyral.Entity",
    message: "tempyral.RequestResponse",
) -> schema.MessageEvent:
    return schema.MessageEvent(
        sender=sender.as_serializable(),
        receiver=receiver.as_serializable(),
        message=message.as_serializable(),
    )


class EventBus:
    def __init__(self):
        self.bus: Queue[schema.StateChangeEvent | schema.MessageEvent] = Queue()

    async def publish(self, event: schema.StateChangeEvent | schema.MessageEvent):
        await self.bus.put(event)

    def empty(self) -> bool:
        return self.bus.empty()


event_bus = EventBus()
