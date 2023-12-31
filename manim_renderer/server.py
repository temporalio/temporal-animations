from typing import List

from manim import LEFT, Mobject

import tempyral
from manim_renderer import mobject
from manim_renderer.entity import ProxyEntityWithChildren
from manim_renderer.history import History


class Server(ProxyEntityWithChildren[tempyral.Server, tempyral.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def render(self, entity: tempyral.Server) -> Mobject:
        return self.with_time(mobject.actor("Temporal Server"), entity)

    @staticmethod
    def get_child_entities(entity: tempyral.Server) -> List[tempyral.History]:
        return [w.history for w in entity.namespace.values()]
