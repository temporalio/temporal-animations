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


def make_init_event(
    server: "tempyral.Server",
    apps: list["tempyral.Application"],
    workflow_workers: list["tempyral.WorkflowWorker"],
    activity_workers: list["tempyral.ActivityWorker"],
) -> schema.InitEvent:
    return schema.InitEvent(
        server=server.as_serializable(),
        apps=[a.as_serializable() for a in apps],
        workflow_workers=[w.as_serializable() for w in workflow_workers],
        activity_workers=[w.as_serializable() for w in activity_workers],
    )


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
    async def publish(self, event: schema.Event):
        print(event.model_dump_json())


event_bus = EventBus()
