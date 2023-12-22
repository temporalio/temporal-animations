"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from manim import DL, DOWN, DR
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import (
    RIGHT,
    UL,
    UP,
    UR,
    WHITE,
    Animation,
    ApplyMethod,
    Mobject,
    Rectangle,
    Scene,
    Text,
    Transform,
    VDict,
    VGroup,
)

from tempyral import simulation
from tempyral.event_bus import MessageEvent, StateChangeEvent


class ManimEntity(ABC):
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.m = self.newm()  # Current visual representation

    @abstractmethod
    def newm(self) -> Mobject:
        """Compute new visual representation given entity state."""
        ...

    def render(self, animate=True):
        newm = self.newm()
        newm.move_to(self.m.get_center())
        if animate:
            self.scene.play(Transform(self.m, newm))
        else:
            self.m.become(newm)

    def send_message(
        self,
        message: "ManimEntity",
        receiver: "ManimEntity",
        anim: Optional[Animation],
    ):
        """
        Animate sending a message.
        """
        self.render()
        self.scene.play(anim)
        self.scene.remove(message.m)
        receiver.render()


class HistoryEvents(ManimEntity):
    def __init__(
        self,
        events: List[simulation.HistoryEvent],
        scene: Scene,
    ):
        super().__init__(scene)
        self.events = events

    def newm(self) -> Mobject:
        font_size = 16
        width = Text("_" * 30, font_size=font_size).width
        events = self.eventsm(self.events, font_size)
        rect = Rectangle(
            width=max(width, events.width) + 0.5,
            height=events.height + 0.5,
            color=WHITE,
        )
        if self.events:
            rect.surround(events)

        return VGroup(rect, events)

    @staticmethod
    def eventsm(events: List[simulation.HistoryEvent], font_size=16) -> Mobject:
        return VGroup(
            *[
                Text(
                    e.event_type.value,
                    font_size=font_size,
                    color=GREEN if e.seen_by_sticky_worker else RED,
                )
                for e in events
            ]
        ).arrange(DOWN, center=True, aligned_edge=LEFT)


class WorkflowTask(HistoryEvents):
    def newm(self) -> Mobject:
        events = super().newm()
        task = Text("WFT", font_size=16)
        return VGroup(task, events).arrange()


class ApplicationRequest(ManimEntity):
    def __init__(
        self,
        request_type: simulation.ApplicationRequestType,
        scene: Scene,
    ) -> None:
        super().__init__(scene)
        self.request_type = request_type

    def newm(self) -> Mobject:
        return Text(self.request_type.value, font_size=16)


class WorkflowWorker(ManimEntity):
    def newm(self) -> Mobject:
        return Text("Workflow Worker", font_size=24)


class Server(ManimEntity):
    def newm(self) -> Mobject:
        server = Text("Server", font_size=24)
        events = HistoryEvents.eventsm(self.history.events)
        return VDict({"server": server, "history": events}).arrange(UP)  # type: ignore

    async def handle_message_event(self, event: MessageEvent):
        if (type(event.sender), type(event.receiver)) == (Server, WorkflowWorker):
            msg = WorkflowTask(event.data["new_events"], self.scene)
        else:
            type_names = type(event.sender).__name__, type(event.receiver).__name__
            raise ValueError(f"Unsupported (sender, receiver) types: {type_names}")

        msg.m.next_to(self.m["history"], RIGHT)
        return self.send_message(
            event.sender,
            event.receiver,
            ApplyMethod(msg.m.move_to, event.receiver.m.get_edge_center(UP)),
        )


class Application(ManimEntity, simulation.Application):
    async def start_workflow(self, server: Server):
        _, pre, post = super().start_workflow(server)
        request = ApplicationRequest(
            simulation.ApplicationRequestType.START_WORKFLOW, self.scene
        )
        request.m.next_to(self.m.get_edge_center(UP), direction=LEFT)
        return self.send_message(
            request,
            pre,
            post,
            server,
            ApplyMethod(request.m.move_to, server.m.get_edge_center(LEFT)),
        )

    def newm(self) -> Mobject:
        return Text("Application", font_size=24)
