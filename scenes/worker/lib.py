from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, ClassVar

from manim import Animation, Mobject, Scene, animation


@dataclass
class Entity(ABC):
    """
    An entity participating in the scene.

    This is a manim Mobject (self.mobj) that knows how to re-render itself.
    """

    # A queue of lazily-evaluated animations to play after the entity is rendered.
    animations: deque[Callable[[], Animation]] = field(default_factory=deque)

    # All entities have a shared reference to the current Manim scene.
    scene: ClassVar["EntityScene"]

    def __post_init__(self, **kwargs) -> None:
        self.mobj = self.render(**kwargs)

    @abstractmethod
    def render(self, **kwargs) -> Mobject:
        """Compute new visual representation given kwargs data."""
        ...

    def render_to_screen(self, **kwargs):
        """
        Mutate `self.mobj` so that it represents the current state of `entity` and update the scene.
        """
        self.mobj.become(self.render(**kwargs).move_to(self.mobj))
        while self.animations:
            animation = self.animations.popleft()()
            print(f"playing animation {animation} for {self}")
            self.scene.play(animation)


@dataclass
class EntityScene(Scene):
    entities: dict[str, Entity] = field(default_factory=dict)

    def __post_init__(self):
        super().__init__()

    def render_to_screen(self):
        for entity in self.entities.values():
            entity.render_to_screen()
