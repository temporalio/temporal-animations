"""
Manim representations of Temporal entities.
"""
from abc import ABC, abstractmethod
from asyncio import QueueEmpty
from typing import Any, Dict, Generic, List, Type, TypeVar, Union

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
    Indicate,
    Mobject,
    Rectangle,
    Scene,
    Text,
    Transform,
    VDict,
    VGroup,
)

from tempyral import simulation
from tempyral.event_bus import MessageEvent, StateChangeEvent, event_bus

E = TypeVar("E", bound=simulation.Entity)


class VisualElement(ABC):
    """
    An element that participates visually in the scene.
    """

    def __init__(self, scene: Scene) -> None:
        self.m = self.newm()  # Current visual representation
        self.scene = scene

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
        self.scene.wait(0.2)

    def handle_change_data(self, data: Dict[str, Any]):
        pass


class ProxyEntity(Generic[E], VisualElement):
    """
    A VisualElement that has a counterpart entity of type E in the simulation.
    """

    def __init__(self, entity: E, scene: Scene) -> None:
        self.e = entity
        super().__init__(scene)
        assert (
            entity not in proxy_registry
        ), "Simulation entities may have one manim proxy only"
        proxy_registry[entity] = self

    def send_message(
        self,
        receiver: "ProxyEntity",
        message: VisualElement,
    ):
        """
        Animate sending a message.
        """
        message.m.move_to(self.m)
        # TODO: Choose the start and end points appropriately given the
        # locations of self and receiver.
        self.scene.add(message.m)
        self.scene.play(ApplyMethod(message.m.move_to, receiver.m, run_time=2.0))
        self.scene.remove(message.m)


# A registry allowing us to look up proxies by their simulation counterparts.
proxy_registry: Dict[simulation.Entity, ProxyEntity] = {}


async def handle_simulation_events(scene: Scene):
    while True:
        event = await event_bus.bus.get()
        await _handle_simulation_event(event, scene)


async def drain_simulation_events(scene: Scene):
    try:
        while event := event_bus.bus.get_nowait():
            await _handle_simulation_event(event, scene)
    except QueueEmpty:
        pass


async def _handle_simulation_event(
    event: Union[StateChangeEvent[simulation.Entity], MessageEvent[simulation.Entity]],
    scene: Scene,
):
    match event:
        case StateChangeEvent(entity, data):
            proxy_entity = proxy_registry[entity]
            proxy_entity.render()
            if data:
                proxy_entity.handle_change_data(data)
        case MessageEvent(sender_entity, receiver_entity, data):
            sender, receiver = (
                proxy_registry[sender_entity],
                proxy_registry[receiver_entity],
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
    def __init__(
        self,
        events: List[simulation.HistoryEvent],
        scene: Scene,
    ):
        self.events = events
        super().__init__(scene)

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
    def newm(self) -> Mobject:
        events = super().newm()
        task = Text("WFT", font_size=16)
        return VGroup(task, events).arrange()


class WorkerRequest(VisualElement):
    def __init__(self, name: str, scene: Scene):
        self.name = name
        super().__init__(scene)

    def newm(self) -> Mobject:
        return Text(self.name, font_size=24)


class ApplicationRequest(VisualElement):
    def __init__(
        self,
        request_type: simulation.ApplicationRequestType,
        scene: Scene,
    ) -> None:
        self.request_type = request_type
        super().__init__(scene)

    def newm(self) -> Mobject:
        return Text(self.request_type.name, font_size=24)


class WorkflowWorker(ProxyEntity[simulation.WorkflowWorker]):
    def newm(self) -> Mobject:
        return Text("Workflow Worker", font_size=24)


class Server(ProxyEntity[simulation.Server]):
    def newm(self) -> Mobject:
        server = Text("Server", font_size=24)
        events = HistoryEvents.eventsm(self.e.history.events)
        return VDict({"server": server, "history": events}).arrange(UP)  # type: ignore

    def handle_change_data(self, data: Dict[str, Any]):
        if n := data.get("new_history_events"):
            for new_event in self.m["history"][-n:]:
                self.scene.play(Indicate(new_event))


class Application(ProxyEntity[simulation.Application]):
    def newm(self) -> Mobject:
        return Text("Application", font_size=24)
