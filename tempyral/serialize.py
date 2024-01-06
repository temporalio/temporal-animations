import json
from enum import Enum
from types import NoneType
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    import tempyral


def get_serializable_data(obj: Any) -> dict | list | int | bool | str | None:
    if hasattr(obj, "__publish__"):
        data = {k: get_serializable_data(getattr(obj, k)) for k in obj.__publish__}
        data["_type"] = obj.__class__.__name__
        return data
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


def emit_init_event(
    server: "tempyral.Server",
    apps: list["tempyral.Application"],
    workflow_workers: list["tempyral.WorkflowWorker"],
    activity_workers: list["tempyral.ActivityWorker"],
):
    _emit(
        dict(
            server=get_serializable_data(server),
            apps=[get_serializable_data(a) for a in apps],
            workflow_workers=[get_serializable_data(w) for w in workflow_workers],
            activity_workers=[get_serializable_data(w) for w in activity_workers],
            _type="InitEvent",
        )
    )


def emit_change_event(entity: "tempyral.Entity"):
    _emit(dict(entity=get_serializable_data(entity), _type="StateChangeEvent"))


def emit_message_event(
    sender: "tempyral.Entity",
    receiver: "tempyral.Entity",
    message: "tempyral.RequestResponse | tempyral.Response",
):
    _emit(
        dict(
            sender=get_serializable_data(sender),
            receiver=get_serializable_data(receiver),
            message=get_serializable_data(message),
            _type="MessageEvent",
        )
    )


def _emit(data: dict[str, Any]):
    print(json.dumps(data, sort_keys=True))
