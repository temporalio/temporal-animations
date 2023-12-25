from typing import Type

from manim import Scene

from tempyral import log
from tempyral.animation.application import Application, ApplicationRequest
from tempyral.animation.entity import ProxyEntity, VisualElement, proxy_entity_registry
from tempyral.animation.server import Server
from tempyral.animation.worker import WorkerRequest, WorkflowTask, WorkflowWorker
from tempyral.event_bus import (
    MessageEvent,
    StateChangeEvent,
    TerminateSimulation,
    event_bus,
)


def set_scene(scene: Scene):
    VisualElement.scene = scene


async def process_simulation_events(scene: Scene):
    while True:
        match await event_bus.bus.get():
            case StateChangeEvent(entity, data):
                log(f"{entity} {data}", "A: handle change event")
                proxy_entity = proxy_entity_registry.get(entity)
                proxy_entity.render(entity)
                if data:
                    proxy_entity.handle_change_data(data)
            case MessageEvent(sender_entity, receiver_entity, data):
                log(f"{sender_entity} -> {receiver_entity}", "A: handle message event")
                sender, receiver = (
                    proxy_entity_registry.get(sender_entity),
                    proxy_entity_registry.get(receiver_entity),
                )
                msg_cls = _get_message_cls_for(sender, receiver)
                msg = msg_cls(**data)
                sender.send_message(receiver, msg)
            case TerminateSimulation():
                break


def _get_message_cls_for(
    sender: ProxyEntity, receiver: ProxyEntity
) -> Type[VisualElement]:
    sender_cls, receiver_cls = type(sender), type(receiver)
    if (sender_cls, receiver_cls) == (Application, Server):
        return ApplicationRequest
    elif (sender_cls, receiver_cls) == (Server, WorkflowWorker):
        return WorkflowTask
    elif (sender_cls, receiver_cls) == (WorkflowWorker, Server):
        return WorkerRequest
    else:
        raise ValueError(
            f"Unsupported (sender, receiver) types: {(sender_cls.__name__, receiver_cls.__name__)}"
        )
