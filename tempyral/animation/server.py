from typing import Any, Dict

from manim import DOWN, RIGHT, UL, UP, Indicate, Mobject, Scene, Text

from tempyral import simulation
from tempyral.animation.entity import ProxyEntity
from tempyral.animation.history import History


class Server(ProxyEntity[simulation.Server]):
    def __init__(self, entity: simulation.Server) -> None:
        super().__init__(entity)
        self.histories = [History(h, self) for h in entity.namespace]

    def render(self, entity: simulation.Server, animate=True):
        histories = entity.namespace
        assert len(histories) >= len(self.histories)
        for h in histories[len(self.histories) :]:
            self.append(h)
        for e, e_entity in zip(self.histories, histories):
            e.render(e_entity)
        super().render(entity)

    def append(self, entity: simulation.History):
        event = History(entity, self)
        self.move_history_into_position(event.m)
        self.histories.append(event)

    def move_history_into_position(self, newm: Mobject) -> Mobject:
        if not self.histories:
            return newm.next_to(self.m, DOWN).align_to(self.m, RIGHT)
        else:
            last = self.histories[-1].m
            return newm.next_to(last, DOWN).align_to(last, RIGHT)

    @staticmethod
    def newm(_: simulation.Server) -> Mobject:
        return Text("Server", font_size=24)

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            try:
                [history] = self.histories
            except ValueError:
                raise ValueError("Multiple workflow histories not supported")
            for new_event in history.events[-n:]:
                self.scene.play(Indicate(new_event.m))
