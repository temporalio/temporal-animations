from typing import List

from manim import DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import UL, Mobject, Text, VGroup

from tempyral import simulation
from tempyral.animation.entity import FONT_SIZE_MEDIUM, ProxyEntity, VisualElement


class HistoryEvents(VisualElement):
    @staticmethod
    def newm(
        events: List[simulation.HistoryEvent], font_size=FONT_SIZE_MEDIUM
    ) -> Mobject:
        return VGroup(
            *(
                Text(
                    e.event_type.name,
                    font_size=font_size,
                    color=GREEN if e.seen_by_sticky_worker else RED,
                )
                for e in events
            )
        ).arrange(DOWN, center=True, aligned_edge=LEFT)


class History(ProxyEntity[simulation.History]):
    @staticmethod
    def newm(history: simulation.History) -> Mobject:
        return HistoryEvents.newm(history.events)

    def move_into_position(self, newm: Mobject) -> Mobject:
        return newm.to_corner(UL)
