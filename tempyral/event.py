import json
from typing import TYPE_CHECKING, Any

from tempyral.entity import to_serializable

if TYPE_CHECKING:
    import tempyral


def emit_init_event(
    server: "tempyral.Server",
    apps: list["tempyral.Application"],
    workflow_workers: list["tempyral.WorkflowWorker"],
    activity_workers: list["tempyral.ActivityWorker"],
):
    _emit(
        dict(
            server=to_serializable(server),
            apps=[to_serializable(a) for a in apps],
            workflow_workers=[to_serializable(w) for w in workflow_workers],
            activity_workers=[to_serializable(w) for w in activity_workers],
            _type="InitEvent",
        )
    )


def emit_change_event(entity: "tempyral.Entity"):
    _emit(dict(entity=to_serializable(entity), _type="StateChangeEvent"))


def emit_message_event(
    sender: "tempyral.Entity",
    receiver: "tempyral.Entity",
    message: "tempyral.RequestResponse | tempyral.Response",
):
    _emit(
        dict(
            sender=to_serializable(sender),
            receiver=to_serializable(receiver),
            message=to_serializable(message),
            _type="MessageEvent",
        )
    )


def _emit(data: dict[str, Any]):
    print(json.dumps(data, sort_keys=True))
