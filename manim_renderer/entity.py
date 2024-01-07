"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod, abstractstaticmethod
from enum import Enum
from typing import Generic, Iterable, Self, Type, TypeVar

import numpy as np
from manim import (
    DOWN,
    ORIGIN,
    RIGHT,
    SMALL_BUFF,
    Animation,
    FadeOut,
    Indicate,
    Mobject,
    Scene,
    Text,
    VGroup,
    VMobject,
)
from manim.typing import Point3D, Vector3

from common.utils import notnull
from manim_renderer import style
from schema import schema

E = TypeVar("E", bound=schema.Entity)

from manim_renderer.manim_shims import AnimationGroup, ApplyMethod, Transform


class MessageStage(Enum):
    Request = 1
    Response = 2


class VisualElement(ABC):
    """
    An entity participating in the scene.

    This is a manim Mobject (self.mobj) that knows how to re-render itself.
    """

    scene = Scene()

    def __init__(self, **kwargs) -> None:
        self.mobj = self.render(**kwargs)  # Current visual representation

    @abstractmethod
    def render(self, **kwargs) -> Mobject:
        """Compute new visual representation given kwargs data."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Root(VisualElement):
    def render(self) -> Mobject:
        return Mobject()


root = Root()


class ProxyEntity(Generic[E], VisualElement):
    """
    A VisualElement that has a counterpart entity of type E in the simulation.
    """

    def __init__(self, entity: E, parent: VisualElement = root) -> None:
        self.parent = parent
        self.dock_direction = ORIGIN
        self.mobj = self.render(entity)  # Current visual representation
        proxy_entity_registry.put(entity, self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    def set_dock_direction(self, direction: Vector3) -> Self:
        self.dock_direction = direction
        return self

    def dock_point(self) -> Point3D:
        return (
            self.mobj.get_edge_center(self.dock_direction) + 0.5 * self.dock_direction
        )

    def get_message_start(self, _: schema.RequestResponse) -> Point3D:
        return self.mobj.get_center()

    def get_message_end(self, _: schema.RequestResponse) -> Point3D:
        return self.dock_point()

    @abstractmethod
    def render(self, entity: E) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def render_to_scene(self, entity: E):
        """
        Mutate `self.mobj` so that it represents the current state of `entity` and update the scene.
        """
        self.mobj.become(self.render(entity).move_to(self.mobj))

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: "ProxyEntity",
        message_entity: schema.RequestResponse,
    ) -> tuple[Animation, Animation, Animation | None]:
        """
        Create (but do not play) animations for sending a message.
        """
        match message_entity.stage:
            case schema.RequestResponseStage.Request:
                return self.send_request(receiver, message, message_entity)
            case schema.RequestResponseStage.Response:
                return self.send_response(receiver, message, message_entity)
            case _:
                raise TypeError

    def send_request(
        self,
        receiver: "ProxyEntity",
        message: "ProxyEntity[schema.RequestResponse]",
        message_entity: schema.RequestResponse,
    ) -> tuple[Animation, Animation, Animation | None]:
        """
        Create (but do not play) animations for sending the request stage of a message.
        """
        self.scene.add(message.mobj)
        msg_start, msg_end = (
            self.get_message_start(message_entity),
            receiver.get_message_end(message_entity),
        )
        halfway = tuple(np.array(list(msg_start + msg_end)) / 2.0)
        self.pending_request, halfway_ray, full_ray = [
            style.pending_request_ray(
                start=msg_start,
                end=end,
            )
            for end in [msg_start, halfway, msg_end]
        ]

        return (
            AnimationGroup(
                ApplyMethod(message.mobj.move_to, halfway),
                Transform(self.pending_request, halfway_ray),
            ),
            AnimationGroup(
                ApplyMethod(message.mobj.move_to, msg_end),
                Transform(self.pending_request, full_ray),
            ),
            None,
        )

    def send_response(
        self,
        receiver: "ProxyEntity",
        message: "ProxyEntity",
        message_entity: schema.RequestResponse,
    ) -> tuple[Animation, Animation, Animation | None]:
        """
        Create (but do not play) animations for sending the response stage of a message.
        """
        msg_start, msg_end = (
            self.get_message_end(message_entity),
            receiver.get_message_start(message_entity),
        )
        halfway = tuple(np.array(list(msg_start + msg_end)) / 2.0)

        # TODO: Make `pending_request` part of the type and use for all messages
        if not hasattr(receiver, "pending_request"):
            return (
                ApplyMethod(message.mobj.move_to, halfway),
                ApplyMethod(message.mobj.move_to, msg_end),
                FadeOut(message.mobj),
            )

        halfway_ray, zero_ray = [
            style.pending_request_ray(start=msg_end, end=end)
            for end in [halfway, msg_end]
        ]

        return (
            AnimationGroup(
                ApplyMethod(message.mobj.move_to, halfway),
                Transform(receiver.pending_request, halfway_ray),
            ),
            AnimationGroup(
                ApplyMethod(message.mobj.move_to, msg_end),
                Transform(receiver.pending_request, zero_ray),
            ),
            FadeOut(message.mobj),
        )

    def play_all_send_message_animations(
        self,
        first_halves: Iterable[Animation],
        second_halves: Iterable[Animation],
        fade_outs: Iterable[Animation | None],
    ):
        """
        Play concurrent message animations.
        """
        self.scene.play(*first_halves)
        self.scene.wait(0.5)
        self.scene.play(*second_halves)
        if fade_outs := list(filter(None, fade_outs)):
            self.scene.play(*fade_outs)
        self.scene.wait()

    def with_time(self, mobj: Mobject, entity: E) -> VMobject:
        return VGroup(
            mobj,
            Text(
                f"[{entity.time}]",
                font_size=8,
                font=style.FONT_CODE,
            ),
        ).arrange(RIGHT, buff=0.05, aligned_edge=DOWN)


F = TypeVar("F", bound=schema.Entity)
Q = TypeVar("Q", bound=ProxyEntity)


class ProxyEntityWithChildren(
    ProxyEntity,
    Generic[E, F, Q],
):
    """
    This class models the situation where a proxy entity has an append-only list
    of child proxy entities. Examples include:
    - Server has a list of Histories
    - A History has a list of HistoryEvents
    - A WorkflowWorker has a list of Workflows
    """

    child_cls: Type[Q]
    child_align_direction: Vector3

    def __init__(self, entity: E, parent: VisualElement = root) -> None:
        super().__init__(entity, parent=parent)
        self.children: list[Q] = []
        for e in self.get_child_entities(entity):
            self.append_child(e)

    @abstractstaticmethod
    def get_child_entities(entity: E) -> list[F]:  # type: ignore (bug in Pyright?)
        ...

    def render_to_scene(self, entity: E):
        n = len(self.children)
        child_entities = self.get_child_entities(entity)
        for new in child_entities[n:]:
            self.append_child(new)

        prev = self
        for child, child_entity in zip(self.children, child_entities):
            child.mobj.next_to(prev.mobj, DOWN, buff=SMALL_BUFF).align_to(
                prev.mobj, self.child_align_direction
            )
            child.render_to_scene(child_entity)
            prev = child

        for new in self.children[n:]:
            self.scene.play(notnull(Indicate(new.mobj)))

        super().render_to_scene(entity)

    def append_child(self, child_entity: F):
        child = self.child_cls(child_entity, parent=self)
        self.scene.add(child.mobj)
        self.children.append(child)


class ProxyEntityRegistry(Generic[E]):
    """
    A registry allowing us to look up proxies by their simulation counterparts.
    """

    def __init__(self):
        self._registry: dict[int, ProxyEntity] = {}

    def put(self, entity: E, proxy: ProxyEntity[E]) -> None:
        key = entity.hash_key()
        if key in self._registry:
            assert (
                self._registry[key] == proxy
            ), "Simulation entities may have one manim proxy only"
        else:
            self._registry[key] = proxy

    def get(self, entity: E) -> ProxyEntity[E]:
        return self._registry[entity.hash_key()]


proxy_entity_registry = ProxyEntityRegistry()
