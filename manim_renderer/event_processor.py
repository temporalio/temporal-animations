from typing import Iterable, Tuple, Type

from manim import Animation, Scene

from manim_renderer.application import ApplicationRequest
from manim_renderer.entity import ProxyEntity, VisualElement, proxy_entity_registry
from manim_renderer.worker import (
    ActivityTaskCompleted,
    ActivityTaskRequest,
    WorkflowTaskCompleted,
)
from manim_renderer.workflow_task import WorkflowTaskRequest
from schema import schema


def set_scene(scene: Scene):
    VisualElement.scene = scene


def lamport_time(event: schema.Event) -> int:
    match event:
        case schema.StateChangeEvent():
            return event.entity.time
        case schema.MessageEvent():
            return event.sender.time
        case schema.InitEvent():
            raise ValueError("Invalid event")


def render_simulation_events(events: Iterable[schema.Event]):
    animations: list[Iterable[Animation | None]] = []

    def flush_animations():
        if animations:
            sender.play_all_send_message_animations(*zip(*animations))
            animations.clear()

    serial = False
    curr_time = -1
    for event in sorted(events, key=lamport_time):
        match event:
            case schema.StateChangeEvent():
                if event.entity.time > curr_time:
                    flush_animations()
                    curr_time = event.entity.time

                proxy_entity = proxy_entity_registry.get(event.entity)
                proxy_entity.render_to_scene(event.entity)
            case schema.MessageEvent():
                (sender, message, receiver) = _get_proxy_entities(
                    event.sender, event.message, event.receiver
                )

                if serial or event.message.time > curr_time:
                    flush_animations()
                    curr_time = event.message.time

                animations.append(sender.send_message(receiver, message, event.message))

    flush_animations()


def _get_proxy_entities(
    sender_entity: schema.Entity,
    message_entity: schema.RequestResponse,
    receiver_entity: schema.Entity,
) -> Tuple[ProxyEntity, ProxyEntity[schema.RequestResponse], ProxyEntity]:
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
        proxy_entity_registry.put(message_entity, msg)
    return sender, msg, receiver


def _get_message_cls_for(
    sender_entity: schema.Entity,
    message_entity: schema.RequestResponse,
) -> Type[ProxyEntity]:
    match message_entity, sender_entity:
        case (schema.ApplicationRequest(), _):
            return ApplicationRequest
        case (schema.WorkerPollRequest(), schema.WorkflowWorker()):
            return WorkflowTaskRequest
        case (schema.WorkerRequest(), schema.WorkflowWorker()):
            return WorkflowTaskCompleted
        case (schema.WorkerPollRequest(), schema.ActivityWorker()):
            return ActivityTaskRequest
        case (schema.WorkerRequest(), schema.ActivityWorker()):
            return ActivityTaskCompleted
        case _:
            raise ValueError(
                f"Unsupported (message, sender) types: {(type(message_entity).__name__, type(sender_entity).__name__)}"
            )
