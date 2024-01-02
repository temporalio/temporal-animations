from typing import List

from manim import LEFT, Mobject
from manim.typing import Point3D

import tempyral
from manim_renderer import style
from manim_renderer.entity import ProxyEntityWithChildren
from manim_renderer.history import History


class Server(ProxyEntityWithChildren[tempyral.Server, tempyral.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def render(self, entity: tempyral.Server) -> Mobject:
        return self.with_time(style.actor("Temporal Server"), entity)

    @staticmethod
    def get_child_entities(entity: tempyral.Server) -> List[tempyral.History]:
        return [w.history for w in entity.namespace.values()]

    def get_message_end(self, message_entity: tempyral.RequestResponse) -> Point3D:
        if isinstance(message_entity, tempyral.WorkerPollRequest):
            return self.mobj.get_center()
        else:
            return super().get_message_end(message_entity)
