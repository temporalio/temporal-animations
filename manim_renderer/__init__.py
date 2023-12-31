from typing import Type

from manim import Scene

from event_bus import MessageEvent, StateChangeEvent, TerminateSimulation, event_bus
from log import log
from manim_renderer.application import Application, ApplicationRequest
from manim_renderer.entity import ProxyEntity, VisualElement, proxy_entity_registry
from manim_renderer.server import Server
from manim_renderer.worker import (
    ActivityTask,
    ActivityTaskCompleted,
    ActivityWorker,
    WorkerRequest,
    WorkflowTask,
    WorkflowWorker,
)


def set_scene(scene: Scene):
    log("\n" * 50, "")
    VisualElement.scene = scene


async def process_simulation_events():
    curr_time = 0
    animations = []
    while True:
        match await event_bus.bus.get():
            case StateChangeEvent(entity):
                log(f"{entity}", "A: handle change event")
                proxy_entity = proxy_entity_registry.get(entity)
                proxy_entity.render_to_scene(entity)
            case MessageEvent(sender_entity, receiver_entity, msg_entity):
                log(f"{sender_entity} -> {receiver_entity}", "A: handle message event")
                sender, receiver = (
                    proxy_entity_registry.get(sender_entity),
                    proxy_entity_registry.get(receiver_entity),
                )
                try:
                    msg = proxy_entity_registry.get(msg_entity)
                except KeyError:
                    msg_cls = _get_message_cls_for(sender, receiver)
                    msg = msg_cls(entity=msg_entity)
                    proxy_entity_registry.set(msg_entity, msg)

                animations.append(sender.send_message(receiver, msg))
                if msg_entity.time > curr_time:
                    sender.play_all_send_message_animations(*zip(*animations))
                    animations.clear()
                    curr_time = msg_entity.time

            case TerminateSimulation():
                break


def _get_message_cls_for(
    sender: ProxyEntity, receiver: ProxyEntity
) -> Type[ProxyEntity]:
    match (type(sender), type(receiver)):
        case sr if sr == (Application, Server):
            return ApplicationRequest
        case sr if sr == (Server, Application):
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
