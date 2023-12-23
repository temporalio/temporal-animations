"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod
from asyncio import QueueEmpty
from typing import Any, Dict, Generic, List, Type, TypedDict, TypeVar, Union

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
    ApplyMethod,
    Code,
    Indicate,
    Mobject,
    Rectangle,
    Scene,
    Text,
    Transform,
    VDict,
    VGroup,
)
from manim.typing import Point3D

from tempyral import log, simulation
from tempyral.event_bus import MessageEvent, StateChangeEvent, event_bus

E = TypeVar("E", bound=simulation.Entity)


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


async def handle_simulation_events(scene: Scene):
    while True:
        event = await event_bus.bus.get()
        await _handle_simulation_event(event, scene)


async def drain_simulation_events(scene: Scene):
    try:
        while event := event_bus.bus.get_nowait():
            log(f"{event}", "A: drain: handle event")
            await _handle_simulation_event(event, scene)
    except QueueEmpty:
        pass


async def _handle_simulation_event(
    event: Union[StateChangeEvent[simulation.Entity], MessageEvent[simulation.Entity]],
    scene: Scene,
):
    match event:
        case StateChangeEvent(entity, data):
            log(f"{entity} {data}", "A: handle change event")
            proxy_entity = proxy_registry.get(entity)
            proxy_entity.render(entity)
            if data:
                proxy_entity.handle_change_data(data)
        case MessageEvent(sender_entity, receiver_entity, data):
            log(f"{sender_entity} -> {receiver_entity}", "A: handle message event")
            sender, receiver = (
                proxy_registry.get(sender_entity),
                proxy_registry.get(receiver_entity),
            )
            msg_cls = get_message_cls_for(sender, receiver)
            msg = msg_cls(scene=scene, **data)
            sender.send_message(receiver, msg)
    scene.wait(0.5)


def get_message_cls_for(
    sender: ProxyEntity, receiver: ProxyEntity
) -> Type[VisualElement]:
    sender_cls, receiver_cls = type(sender), type(receiver)
    if (sender_cls, receiver_cls) == (Application, Server):
        return ApplicationRequest
    elif (sender_cls, receiver_cls) == (Server, WorkflowWorker):
        return WorkflowTask
    elif (sender_cls, receiver_cls) == (WorkflowWorker, Server):
        return WorkerRequest
    else:
        raise ValueError(
            f"Unsupported (sender, receiver) types: {(sender_cls.__name__, receiver_cls.__name__)}"
        )


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
    def eventsm(events: List[simulation.HistoryEvent], font_size=16) -> Mobject:
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


class WorkflowTask(HistoryEvents):
    def newm(self, events: List[simulation.HistoryEvent]) -> Mobject:
        eventsm = super().newm(events)
        task = Text("WFT", font_size=16)
        return VGroup(task, eventsm).arrange()


class WorkerRequest(VisualElement):
    def newm(self, name: str) -> Mobject:
        return Text(name, font_size=24)


class ApplicationRequest(VisualElement):
    def newm(self, request_type: simulation.ApplicationRequestType) -> Mobject:
        return Text(request_type.name, font_size=24)


class WorkflowWorker(ProxyEntity[simulation.WorkflowWorker]):
    def newm(self, entity: simulation.WorkflowWorker) -> Mobject:
        text = Text("Workflow Worker", font_size=24)
        code = Code(code=entity.go, language="go", font_size=12)
        return VGroup(text, code).arrange(DOWN)


class Server(ProxyEntity[simulation.Server]):
    def newm(self, entity: simulation.Server) -> Mobject:
        server = Text("Server", font_size=24)
        events = HistoryEvents.eventsm(entity.history.events)
        return VDict({"server": server, "history": events}).arrange(UP)  # type: ignore

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            for new_event in self.m["history"][-n:]:
                self.scene.play(Indicate(new_event))


class Application(ProxyEntity[simulation.Application]):
    def newm(self, entity: simulation.Application) -> Mobject:
        return Text("Application", font_size=24)
