"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from manim import UP, ApplyMethod, Mobject, Scene, Transform
from manim.typing import Point3D

from tempyral import log, simulation

E = TypeVar("E", bound=simulation.Entity)

MONOSPACE_FONT = "Menlo"
FONT_SIZE_LARGE = 24
FONT_SIZE_MEDIUM = 20
FONT_SIZE_SMALL = 12


class VisualElement(ABC):
    """
    An element that participates visually in the scene.
    """

    def __init__(self, scene: Scene, **kwargs) -> None:
        self.scene = scene
        self.m = self.newm(**kwargs)  # Current visual representation

    @abstractmethod
    def newm(self, **kwargs) -> Mobject:
        """Compute new visual representation given entity state."""
        ...


class ProxyEntity(Generic[E], ABC):
    """
    A VisualElement that has a counterpart entity of type E in the simulation.
    """

    def __init__(self, entity: E, scene: Scene, receive_edge=UP) -> None:
        self.m = self.newm(entity)  # Current visual representation
        self.scene = scene
        self.dock_edge = receive_edge
        proxy_registry.set(entity, self)

    def dock_point(self) -> Point3D:
        return self.m.get_edge_center(self.dock_edge)

    @abstractmethod
    def newm(self, entity: E) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def render(self, entity: E, animate=True):
        log(f"{entity}\n", "A: render")
        newm = self.newm(entity)
        newm.move_to(self.m.get_center())
        if animate:
            self.scene.play(Transform(self.m, newm))
        else:
            self.m.become(newm)
        self.scene.wait(0.2)

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: VisualElement,
    ):
        """
        Animate sending a message.
        """
        log(f"{self} -> {receiver})\n", "A: send_message")
        message.m.next_to(self.dock_point())
        # TODO: Choose the start and end points appropriately given the
        # locations of self and receiver.
        self.scene.add(message.m)
        self.scene.play(
            ApplyMethod(message.m.move_to, receiver.dock_point(), run_time=2.0)
        )
        self.scene.remove(message.m)

    def handle_change_data(self, data: Dict[str, Any]):
        pass


class ProxyRegistry(Generic[E]):
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


proxy_registry = ProxyRegistry()
