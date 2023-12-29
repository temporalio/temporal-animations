"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Any, Dict, Generic, List, Self, Type, TypeVar

import numpy as np
from manim import (
    DOWN,
    ORIGIN,
    SMALL_BUFF,
    ApplyMethod,
    Indicate,
    Mobject,
    Scene,
    Transform,
)
from manim.typing import Point3D, Vector3

from tempyral import log, simulation

E = TypeVar("E", bound=simulation.Entity)


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
        self.mobj = self.render(entity)  # Current visual representation
        self.dock_direction = ORIGIN
        proxy_entity_registry.set(entity, self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    def set_dock_direction(self, direction: Vector3) -> Self:
        self.dock_direction = direction
        return self

    def dock_point(self) -> Point3D:
        return self.mobj.get_edge_center(self.dock_direction)

    @abstractmethod
    def render(self, entity: E) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def update(self, entity: E, animate=False):
        """
        Mutate `self.mobj` so that it represents `entity` and paint the result to screen.
        """
        mobj = self.render(entity).move_to(self.mobj)
        if animate:
            self.scene.play(Transform(self.mobj, mobj))
        else:
            self.mobj.become(mobj)

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: VisualElement,
    ):
        """
        Animate sending a message.
        """
        log(f"{self} -> {receiver}: {message}\n", "A: send_message")
        message.mobj.next_to(self.dock_point())
        # TODO: Choose the start and end points appropriately given the
        # locations of self and receiver.
        self.scene.add(message.mobj)
        halfway = tuple(
            np.array(list(message.mobj.get_center() + receiver.dock_point())) / 2.0
        )
        self.scene.play(ApplyMethod(message.mobj.move_to, halfway))
        self.scene.wait(0.5)
        self.scene.play(ApplyMethod(message.mobj.move_to, receiver.dock_point()))
        self.scene.remove(message.mobj)
        self.scene.wait()


F = TypeVar("F", bound=simulation.Entity)
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

    def update(self, entity: E):
        n = len(self.children)
        child_entities = self.get_child_entities(entity)
        for new in child_entities[n:]:
            self.append_child(new)

        prev = self
        for child, child_entity in zip(self.children, child_entities):
            child.mobj.next_to(prev.mobj, DOWN, buff=SMALL_BUFF).align_to(
                prev.mobj, self.child_align_direction
            )
            child.update(child_entity)
            prev = child

        for new in self.children[n:]:
            self.scene.play(Indicate(new.mobj))

        super().update(entity)

    def append_child(self, child_entity: F):
        child = self.child_cls(child_entity, parent=self)
        self.scene.add(child.mobj)
        self.children.append(child)


class ProxyEntityRegistry(Generic[E]):
    """
    A registry allowing us to look up proxies by their simulation counterparts.
    """

    def __init__(self):
        self._registry: Dict[simulation.Entity, ProxyEntity] = {}

    def set(self, entity: E, proxy: ProxyEntity[E]) -> None:
        assert (
            entity not in self._registry
        ), "Simulation entities may have one manim proxy only"
        self._registry[entity] = proxy

    def get(self, entity: E) -> ProxyEntity[E]:
        return self._registry[entity]


proxy_entity_registry = ProxyEntityRegistry()
