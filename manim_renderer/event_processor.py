from typing import Iterable, Tuple, Type

from manim import Animation, Scene

from common.logger import log
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


def render_simulation_events(events: Iterable[schema.Event]):
    curr_time = -1
    animations: list[Iterable[Animation | None]] = []
    serial = True
    n = 400
    for event in events:
        match event:
            case schema.StateChangeEvent():
                proxy_entity = proxy_entity_registry.get(event.entity)
                proxy_entity.render_to_scene(event.entity)
            case schema.MessageEvent():
                sender, receiver, message = _get_proxy_entities(
                    event.sender, event.receiver, event.message
                )

                log(
                    f"{event.message.id}: {sender} -> {receiver}: {message}",
                    "A: render  message",
                )

                animations.append(sender.send_message(receiver, message, event.message))

                if serial or event.message.time > curr_time:
                    sender.play_all_send_message_animations(*zip(*animations))
                    animations.clear()
                    curr_time = event.message.time

                if not (n := n - 1):
                    break


def _get_proxy_entities(
    sender_entity: schema.Entity,
    receiver_entity: schema.Entity,
    message_entity: schema.RequestResponse,
) -> Tuple[ProxyEntity, ProxyEntity, ProxyEntity[schema.RequestResponse]]:
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
    return sender, receiver, msg


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
