from typing import List

from manim import DOWN, LEFT, UP, Mobject, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.entity import ProxyEntityWithChildren
from manim_renderer.history import History


class Server(ProxyEntityWithChildren[tempyral.Server, tempyral.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def render(self, entity: tempyral.Server) -> Mobject:
        in_flight_request_types = VGroup(
            *(mobject.message(m) for m in entity.in_flight_application_request_types)
        ).arrange(DOWN)
        return VGroup(
            mobject.actor("Temporal Server"), in_flight_request_types
        ).arrange(UP)

    @staticmethod
    def get_child_entities(entity: tempyral.Server) -> List[tempyral.History]:
        return [w.history for w in entity.namespace.values()]
