from typing import Type

from manim import Scene

from tempyral import log
from tempyral.animation.application import Application, ApplicationRequest
from tempyral.animation.entity import ProxyEntity, VisualElement, proxy_entity_registry
from tempyral.animation.server import Server
from tempyral.animation.worker import (
    ActivityTask,
    ActivityTaskCompleted,
    ActivityWorker,
    WorkerRequest,
    WorkflowTask,
    WorkflowWorker,
)
from tempyral.event_bus import (
    MessageEvent,
    StateChangeEvent,
    TerminateSimulation,
    event_bus,
)


def set_scene(scene: Scene):
    log("\n" * 50, "")
    VisualElement.scene = scene


async def process_simulation_events():
    while True:
        match await event_bus.bus.get():
            case StateChangeEvent(entity):
                log(f"{entity}", "A: handle change event")
                proxy_entity = proxy_entity_registry.get(entity)
                proxy_entity.render(entity)
            case MessageEvent(sender_entity, receiver_entity, data):
                log(f"{sender_entity} -> {receiver_entity}", "A: handle message event")
                sender, receiver = (
                    proxy_entity_registry.get(sender_entity),
                    proxy_entity_registry.get(receiver_entity),
                )
                msg_cls = _get_message_cls_for(sender, receiver)
                msg = msg_cls(**data)  # TODO: type safety
                sender.send_message(receiver, msg)
            case TerminateSimulation():
                break


def _get_message_cls_for(
    sender: ProxyEntity, receiver: ProxyEntity
) -> Type[VisualElement]:
    match (type(sender), type(receiver)):
        case sr if sr == (Application, Server):
            return ApplicationRequest
        case sr if sr == (WorkflowWorker, Server):
            return WorkerRequest
        case sr if sr == (ActivityWorker, Server):
            return ActivityTaskCompleted
        case sr if sr == (Server, WorkflowWorker):
            return WorkflowTask
        case sr if sr == (Server, ActivityWorker):
            return ActivityTask
        case _:
            raise ValueError(
                f"Unsupported (sender, receiver) types: {(type(sender).__name__, type(receiver).__name__)}"
            )
