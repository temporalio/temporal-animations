from typing import List

from manim import DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import WHITE, Mobject, Rectangle, Text, VGroup

from tempyral import simulation
from tempyral.animation.entity import FONT_SIZE_MEDIUM, VisualElement


class HistoryEvents(VisualElement):
    def newm(self, events: List[simulation.HistoryEvent]) -> Mobject:
        font_size = 16
        width = Text("_" * 30, font_size=font_size).width
        eventsm = self.eventsm(events, font_size)
        rect = Rectangle(
            width=max(width, eventsm.width) + 0.5,
            height=eventsm.height + 0.5,
            color=WHITE,
        )
        if events:
            rect.surround(eventsm)

        return VGroup(rect, eventsm)

    @staticmethod
    def eventsm(
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
