"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod, abstractstaticmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Self, Type, TypeVar

import numpy as np
from manim import (
    DOWN,
    ORIGIN,
    RIGHT,
    SMALL_BUFF,
    ApplyMethod,
    Indicate,
    Mobject,
    Scene,
    Text,
    Transform,
    VGroup,
)
from manim.typing import Point3D, Vector3

import tempyral
from log import log
from manim_renderer import style
from manim_renderer.utils import notnull

E = TypeVar("E", bound=tempyral.Entity)


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
        proxy_entity_registry.set(entity, self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    def set_dock_direction(self, direction: Vector3) -> Self:
        self.dock_direction = direction
        return self

    def dock_point(self) -> Point3D:
        return (
            self.mobj.get_edge_center(self.dock_direction) + 0.5 * self.dock_direction
        )

    @abstractmethod
    def render(self, entity: E) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def render_to_scene(self, entity: E, animate=False):
        """
        Mutate `self.mobj` so that it represents the current state of `entity` and update the scene.
        """
        mobj = self.render(entity).move_to(self.mobj)
        if animate:
            self.scene.play(notnull(Transform(self.mobj, mobj)))
        else:
            self.mobj.become(mobj)

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: "ProxyEntity[tempyral.RequestResponse]",
    ):
        """
        Animate sending a message.
        """
        log(f"{self} -> {receiver}: {message}\n", "A: send_message")
        message.mobj.move_to(self.dock_point())
        # TODO: Choose the start and end points appropriately given the
        # locations of self and receiver.
        self.scene.add(message.mobj)
        halfway = tuple(
            np.array(list(message.mobj.get_center() + receiver.dock_point())) / 2.0
        )
        self.scene.play(notnull(ApplyMethod(message.mobj.move_to, halfway)))
        self.scene.wait(0.5)
        self.scene.play(
            notnull(ApplyMethod(message.mobj.move_to, receiver.dock_point()))
        )
        self.scene.wait()

    def with_time(self, mobj: Mobject, entity: E) -> Mobject:
        return VGroup(
            mobj,
            Text(
                f"[{entity.time}]",
                font_size=8,
                font=style.FONT_CODE,
            ),
        ).arrange(RIGHT, buff=0.05, aligned_edge=DOWN)


F = TypeVar("F", bound=tempyral.Entity)
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

    def __init__(self, entity: Any, parent: VisualElement = root) -> None:
        super().__init__(entity, parent=parent)
        self.children: List[Q] = []
        for e in self.get_child_entities(entity):
            self.append_child(e)

    @abstractstaticmethod
    def get_child_entities(entity: E) -> List[F]:  # type: ignore (bug in Pyright?)
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
        self._registry: Dict[tempyral.Entity, ProxyEntity] = {}

    def set(self, entity: E, proxy: ProxyEntity[E]) -> None:
        if entity in self._registry:
            assert (
                self._registry[entity] == proxy
            ), "Simulation entities may have one manim proxy only"
        else:
            self._registry[entity] = proxy

    def get(self, entity: E) -> ProxyEntity[E]:
        return self._registry[entity]


proxy_entity_registry = ProxyEntityRegistry()
