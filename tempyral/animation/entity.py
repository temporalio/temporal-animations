"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractstaticmethod
from typing import Any, Dict, Generic, List, Self, Type, TypeVar

from manim import (
    DOWN,
    ORIGIN,
    RIGHT,
    UP,
    ApplyMethod,
    Indicate,
    Mobject,
    Scene,
    Transform,
)
from manim.typing import Point3D, Vector3

from tempyral import log, simulation

E = TypeVar("E", bound=simulation.Entity)

MONOSPACE_FONT = "Menlo"
FONT_SIZE_LARGE = 24
FONT_SIZE_MEDIUM = 20
FONT_SIZE_SMALL = 12


class VisualElement(ABC):
    """
    An entity participating in the scene.

    This is a manim Mobject (self.m) that knows how to re-render itself.
    """

    scene = Scene()

    def __init__(self, **kwargs) -> None:
        self.m = self.newm(**kwargs)  # Current visual representation

    @abstractstaticmethod
    def newm(**kwargs) -> Mobject:
        """Compute new visual representation given kwargs data."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Root(VisualElement):
    def newm(self) -> Mobject:
        return Mobject()


root = Root()


class ProxyEntity(Generic[E], VisualElement):
    """
    A VisualElement that has a counterpart entity of type E in the simulation.
    """

    def __init__(self, entity: E, parent: VisualElement = root) -> None:
        self.parent = parent
        self.m = self.newm(entity)  # Current visual representation
        self.dock_direction = ORIGIN
        proxy_entity_registry.set(entity, self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    def set_dock_direction(self, direction: Vector3) -> Self:
        self.dock_direction = direction
        return self

    def dock_point(self) -> Point3D:
        return self.m.get_edge_center(self.dock_direction)

    @staticmethod  # should be abstractstaticmethod but there seems to be a Pyright bug
    def newm(entity: E) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def render(self, entity: E, animate=True):
        """
        Mutate `self.m` so that it represents `entity` and paint the result to screen.
        """
        log(f"{entity}\n", "A: render")
        newm = self.newm(entity).move_to(self.m)
        if animate:
            self.scene.play(Transform(self.m, newm))
        else:
            self.m.become(newm)

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: VisualElement,
    ):
        """
        Animate sending a message.
        """
        log(f"{self} -> {receiver}\n", "A: send_message")
        message.m.next_to(self.dock_point())
        # TODO: Choose the start and end points appropriately given the
        # locations of self and receiver.
        self.scene.add(message.m)
        self.scene.play(
            ApplyMethod(message.m.move_to, receiver.dock_point(), run_time=1.5)
        )
        self.scene.remove(message.m)


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
    - A WorkflowWorker has a list of WorkflowDefinitions
    """

    child_cls: Type[Q]

    def __init__(self, entity: Any, parent: VisualElement = root) -> None:
        super().__init__(entity, parent=parent)
        self.children: List[Q] = []
        for e in self.get_child_entities(entity):
            self.append_child(e)

    @abstractstaticmethod
    def get_child_entities(entity: E) -> List[F]:  # type: ignore (bug in Pyright?)
        ...

    def render(self, entity: E):
        n = len(self.children)
        child_entities = self.get_child_entities(entity)
        for new in child_entities[n:]:
            self.append_child(new)

        prev = self
        for child, child_entity in zip(self.children, child_entities):
            log(
                f"align child {child.m} below {prev.m}: {prev.m.get_center()}",
                "A: render",
            )
            child.m.next_to(prev.m, DOWN).align_to(prev.m, RIGHT)
            child.render(child_entity)
            prev = child

        for new in self.children[n:]:
            self.scene.play(Indicate(new.m))
        super().render(entity)

    def append_child(self, child_entity: F):
        self.children.append(self.child_cls(child_entity, parent=self))


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
