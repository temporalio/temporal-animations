from typing import Any, Dict

from manim import UP, Indicate, Mobject, Text, VDict

from tempyral import simulation
from tempyral.animation.entity import ProxyEntity
from tempyral.animation.history import HistoryEvents


class Server(ProxyEntity[simulation.Server]):
    def newm(self, entity: simulation.Server) -> Mobject:
        server = Text("Server", font_size=24)
        events = HistoryEvents.eventsm(entity.history.events)
        return VDict({"server": server, "history": events}).arrange(UP)  # type: ignore

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            for new_event in self.m["history"][-n:]:
                self.scene.play(Indicate(new_event))
