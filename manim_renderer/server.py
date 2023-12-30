from typing import List

from manim import LEFT, Mobject

import tempyral
from manim_renderer import mobject
from manim_renderer.entity import ProxyEntityWithChildren
from manim_renderer.history import History


class Server(ProxyEntityWithChildren[tempyral.Server, tempyral.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def render(self, _: tempyral.Server) -> Mobject:
        return mobject.actor("Temporal Server")

    @staticmethod
    def get_child_entities(entity: tempyral.Server) -> List[tempyral.History]:
        return [w.history for w in entity.namespace.values()]
