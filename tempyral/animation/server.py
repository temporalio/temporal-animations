from typing import List

from manim import LEFT, Mobject, Text

from tempyral import simulation
from tempyral.animation import mobject
from tempyral.animation.entity import ProxyEntityWithChildren
from tempyral.animation.history import History


class Server(ProxyEntityWithChildren[simulation.Server, simulation.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def newm(self, _: simulation.Server) -> Mobject:
        return mobject.actor("Server")

    @staticmethod
    def get_child_entities(entity: simulation.Server) -> List[simulation.History]:
        return list(entity.namespace.values())
