from typing import Any, Dict

from manim import UL, UP, Indicate, Mobject, Scene, Text

from tempyral import simulation
from tempyral.animation.entity import ProxyEntity
from tempyral.animation.history import History


class Server(ProxyEntity[simulation.Server]):
    def __init__(self, entity: simulation.Server, scene: Scene) -> None:
        super().__init__(entity, scene)
        self.history = History(entity.history, scene)
        self.history.move_into_position(self.history.m)

    def render(self, entity: simulation.Server, animate=True):
        super().render(entity, animate)
        self.history.render(entity.history, animate=True)

    @staticmethod
    def newm(_: simulation.Server) -> Mobject:
        return Text("Server", font_size=24)

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            for new_event in self.history.m[-n:]:
                self.scene.play(Indicate(new_event))
