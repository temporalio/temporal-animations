from typing import Any, Dict, List

from manim import DOWN, RIGHT, UL, UP, Indicate, Mobject, Text

from tempyral import simulation
from tempyral.animation.entity import FONT_SIZE_LARGE, ProxyEntityWithChildren
from tempyral.animation.history import History


class Server(ProxyEntityWithChildren[simulation.Server, simulation.History, History]):
    child_cls = History
    child_align_direction = RIGHT

    @staticmethod
    def newm(_: simulation.Server) -> Mobject:
        return Text("Server", font_size=FONT_SIZE_LARGE)

    @staticmethod
    def get_child_entities(entity: simulation.Server) -> List[simulation.History]:
        return entity.namespace
