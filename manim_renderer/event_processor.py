from asyncio import CancelledError
from typing import Iterable, Tuple, Type, cast

from manim import Animation, Scene

import tempyral
from event_bus import MessageEvent, StateChangeEvent, event_bus
from logger import log
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
    animations: list[Iterable[Animation | None]] = []
    serial = True
    n = 400

    async def process(draining: bool):
        nonlocal n, curr_time
        while not (draining and event_bus.empty()):
            match await event_bus.bus.get():
                case StateChangeEvent(entity):
                    proxy_entity = proxy_entity_registry.get(entity)
                    proxy_entity.render_to_scene(entity)
                case MessageEvent(sender_entity, receiver_entity, msg_entity):
                    sender_entity, receiver_entity, msg_entity = (
                        cast(tempyral.Entity, sender_entity),
                        cast(tempyral.Entity, receiver_entity),
                        cast(tempyral.RequestResponse, msg_entity),
                    )
                    sender, receiver, msg = _get_proxy_entities(
                        sender_entity, receiver_entity, msg_entity
                    )

                    log(
                        f"{msg_entity.id}: {sender_entity} -> {receiver_entity}: {msg_entity}",
                        "A: render  message",
                    )

                    animations.append(sender.send_message(receiver, msg, msg_entity))

                    if serial or msg_entity.time > curr_time:
                        sender.play_all_send_message_animations(*zip(*animations))
                        animations.clear()
                        curr_time = msg_entity.time

                    if not (n := n - 1):
                        break

    try:
        await process(draining=False)
    except CancelledError:
        await process(draining=True)


def _get_proxy_entities(
    sender_entity: tempyral.Entity,
    receiver_entity: tempyral.Entity,
    message_entity: tempyral.RequestResponse,
) -> Tuple[ProxyEntity, ProxyEntity, ProxyEntity[tempyral.RequestResponse]]:
    """
    Obtain renderer proxies for the simulation entities. The two
    actors will be in the registry already (all actors are created
    at scene setup time). The request-response message might be
    new (it's the request stage), or it might be in the registry
    already (it's the response stage).
    """
    sender, receiver = (
        proxy_entity_registry.get(sender_entity),
        proxy_entity_registry.get(receiver_entity),
    )
    try:
        msg = proxy_entity_registry.get(message_entity)
    except KeyError:
        msg_cls = _get_message_cls_for(sender, receiver)
        msg = msg_cls(entity=message_entity)
        msg.mobj.move_to(sender.dock_point())
        proxy_entity_registry.set(message_entity, msg)
    return sender, receiver, msg


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
