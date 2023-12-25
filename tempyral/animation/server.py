from typing import Any, Dict

from manim import UL, UP, Indicate, Mobject, Scene, Text

from tempyral import simulation
from tempyral.animation.entity import ProxyEntity
from tempyral.animation.history import History


class Server(ProxyEntity[simulation.Server]):
    def __init__(self, entity: simulation.Server) -> None:
        super().__init__(entity)
        self.history = History(entity.history.events)

    def render(self, entity: simulation.Server, animate=True):
        super().render(entity, animate)
        self.history.render(entity.history.events)

    @staticmethod
    def newm(_: simulation.Server) -> Mobject:
        return Text("Server", font_size=24)

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            for new_event in self.history.events[-n:]:
                self.scene.play(Indicate(new_event.m))
