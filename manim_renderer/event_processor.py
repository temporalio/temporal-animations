from asyncio import CancelledError
from typing import Iterable, Tuple, Type, cast

from manim import Animation, Scene

import tempyral
from event_bus import MessageEvent, StateChangeEvent, event_bus
from logger import log
from manim_renderer.application import ApplicationRequest
from manim_renderer.entity import ProxyEntity, VisualElement, proxy_entity_registry
from manim_renderer.worker import (
    ActivityTaskCompleted,
    ActivityTaskRequest,
    WorkflowTaskCompleted,
    WorkflowTaskRequest,
)


def set_scene(scene: Scene):
    VisualElement.scene = scene


async def process_simulation_events():
    curr_time = -1
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
        msg.render_to_scene(message_entity)
    except KeyError:
        msg_cls = _get_message_cls_for(sender_entity, message_entity)
        msg = msg_cls(entity=message_entity)
        msg.mobj.move_to(sender.get_message_start(message_entity))
        proxy_entity_registry.set(message_entity, msg)
    return sender, receiver, msg


def _get_message_cls_for(
    sender_entity: tempyral.Entity,
    message_entity: tempyral.RequestResponse,
) -> Type[ProxyEntity]:
    match message_entity, sender_entity:
        case (tempyral.ApplicationRequest(), _):
            return ApplicationRequest
        case (tempyral.WorkerPollRequest(), tempyral.WorkflowWorker()):
            return WorkflowTaskRequest
        case (tempyral.WorkerRequest(), tempyral.WorkflowWorker()):
            return WorkflowTaskCompleted
        case (tempyral.WorkerPollRequest(), tempyral.ActivityWorker()):
            return ActivityTaskRequest
        case (tempyral.WorkerRequest(), tempyral.ActivityWorker()):
            return ActivityTaskCompleted
        case _:
            raise ValueError(
                f"Unsupported (message, sender) types: {(type(message_entity).__name__, type(sender_entity).__name__)}"
            )
