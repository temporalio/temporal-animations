"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Self

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    WHITE,
    ApplyMethod,
    Mobject,
    Rectangle,
    Scene,
    Text,
    Transform,
    VGroup,
)

from tempyral import entity


class ManimEntity(ABC):
    def __init__(self, scene: Scene, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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


class HistoryEvents(ManimEntity, entity.HistoryEvents):
    @classmethod
    def from_entity(cls, scene: Scene, events: List[entity.Event]) -> Self:
        return cls(scene, events)

    def newm(self) -> Mobject:
        events = VGroup(*[Text(e, font_size=16) for e in self.events]).arrange(
            DOWN, center=True, aligned_edge=LEFT
        )
        rect = Rectangle(
            width=events.width + 0.5,
            height=events.height + 0.5,
            color=WHITE,
        )
        if self.events:
            rect.surround(events)

        return VGroup(rect, events)


# TODO: This isn't quite right; e.g. WorkflowTask.from_entity is going be
# executing entity.HistoryEvents code paths.
WorkflowTask = HistoryEvents


class ApplicationRequest(ManimEntity, entity.ApplicationRequest):
    @classmethod
    def from_entity(cls, scene: Scene, events: List[entity.Event]) -> Self:
        return cls(scene, events)

    # TODO: Here we are starting to use the manim objects to store simulation
    # state. We need to (a) represent a request, and the associated state
    # changes, in the simulation world, and (b) extend that with visual
    # representation in the manim world.
    def newm(self) -> Mobject:
        request = Text("Request", font_size=12)
        events = HistoryEvents.from_entity(self.scene, self.events).m
        return VGroup(request, events).arrange()


class WorkflowWorker(ManimEntity, entity.WorkflowWorker):
    def newm(self) -> Mobject:
        return Text("Workflow Worker", font_size=24)


class Server(ManimEntity, entity.Server):
    def newm(self) -> Mobject:
        server = Text("Server", font_size=24)
        history = HistoryEvents.from_entity(self.scene, self.history.events).m
        return VGroup(server, history).arrange()

    def dispatch_wft(self, worker: WorkflowWorker):
        wft_entity, pre, post = super().dispatch_wft(worker)
        wft = WorkflowTask.from_entity(self.scene, wft_entity.events)
        wft.m.move_to(self.m.get_edge_center(RIGHT))
        self.scene.play(ApplyMethod(wft.m.move_to, worker.m))
        self.scene.remove(wft.m)


class Application(ManimEntity, entity.Application):
    def start_workflow(self, server: Server):
        request_entity, pre, post = super().start_workflow(server)
        request = ApplicationRequest.from_entity(self.scene, request_entity.events)
        return self.send_request(request, pre, post, server)

    def send_request(
        self,
        request: ApplicationRequest,
        pre_hook: List[Callable],
        post_hook: List[Callable],
        server: Server,
    ):
        request.m.next_to(self.m.get_edge_center(UP), direction=LEFT)
        self.scene.add(request.m)
        for f in pre_hook:
            f()
        self.render()
        self.scene.play(ApplyMethod(request.m.move_to, server.m.get_edge_center(LEFT)))
        self.scene.remove(request.m)
        for f in post_hook:
            f()
        server.render()

    def newm(self) -> Mobject:
        return Text("Application", font_size=24)
