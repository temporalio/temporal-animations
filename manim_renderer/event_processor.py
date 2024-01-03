from asyncio import CancelledError
from typing import Iterable, Tuple, Type, cast

from manim import Animation, Scene

import tempyral
from common.event_bus import EventBus, MessageEvent, StateChangeEvent, event_bus
from common.logger import log
from manim_renderer.application import ApplicationRequest
from manim_renderer.entity import ProxyEntity, VisualElement, proxy_entity_registry
from manim_renderer.worker import (
    ActivityTaskCompleted,
    ActivityTaskRequest,
    WorkflowTaskCompleted,
    WorkflowTaskRequest,
)

event_bus: EventBus[tempyral.Entity]
type Event = StateChangeEvent[tempyral.Entity] | MessageEvent[tempyral.Entity]


def set_scene(scene: Scene):
    VisualElement.scene = scene


async def process_simulation_events():
    async def collect(draining: bool):
        while not (draining and event_bus.empty()):
            yield await event_bus.bus.get()

    events: list[Event] = []
    try:
        async for e in collect(False):
            events.append(e)
    except CancelledError:
        async for e in collect(True):
            events.append(e)

    _render_simulation_events(events)


def lamport_time(event: Event) -> int:
    match event:
        case StateChangeEvent(entity):
            return entity.time
        case MessageEvent(_, _, msg_entity):
            return msg_entity.time


def _render_simulation_events(
    events: list[StateChangeEvent[tempyral.Entity] | MessageEvent[tempyral.Entity]],
):
    curr_time = -1
    animations: list[Iterable[Animation | None]] = []
    serial = True
    n = 400
    for event in sorted(events, key=lamport_time):
        match event:
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
