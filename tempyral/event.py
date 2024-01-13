import json
from typing import TYPE_CHECKING, Any

from tempyral.entity import to_serializable

if TYPE_CHECKING:
    from tempyral.application import AbstractApplication
    from tempyral.entity import Entity
    from tempyral.nexus import NexusServer, NexusWorker
    from tempyral.request_response import RequestResponse, Response
    from tempyral.server import Server
    from tempyral.worker import ActivityWorker, WorkflowWorker


def _get_init_event_data(
    server: "Server",
    apps: list["AbstractApplication"],
    workflow_workers: list["WorkflowWorker"],
    activity_workers: list["ActivityWorker"],
) -> dict[str, Any]:
    return dict(
        server=to_serializable(server),
        apps=[to_serializable(a) for a in apps],
        workflow_workers=[to_serializable(w) for w in workflow_workers],
        activity_workers=[to_serializable(w) for w in activity_workers],
    )


def emit_init_event(
    server: "Server",
    apps: list["AbstractApplication"],
    workflow_workers: list["WorkflowWorker"],
    activity_workers: list["ActivityWorker"],
):
    _emit(
        dict(
            _get_init_event_data(server, apps, workflow_workers, activity_workers),
            _type="InitEvent",
        )
    )


def emit_nexus_init_event(
    server: "Server",
    apps: list["AbstractApplication"],
    workflow_workers: list["WorkflowWorker"],
    activity_workers: list["ActivityWorker"],
    nexus_server: "NexusServer | None",
    nexus_workers: "list[NexusWorker]",
):
    _emit(
        dict(
            _get_init_event_data(server, apps, workflow_workers, activity_workers),
            nexus_server=to_serializable(nexus_server),
            nexus_workers=[to_serializable(w) for w in nexus_workers],
            _type="NexusInitEvent",
        )
    )


def emit_change_event(entity: "Entity"):
    _emit(dict(entity=to_serializable(entity), _type="StateChangeEvent"))


def emit_message_event(
    sender: "Entity",
    receiver: "Entity",
    message: "RequestResponse | Response",
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
    print(json.dumps(data, sort_keys=True), flush=True)
