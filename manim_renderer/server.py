from manim import LEFT, Mobject
from manim.typing import Point3D

from manim_renderer import style
from manim_renderer.entity import ProxyEntityWithChildren
from manim_renderer.history import History
from schema import schema


class Server(ProxyEntityWithChildren[schema.Server, schema.History, History]):
    child_cls = History
    child_align_direction = LEFT

    def render(self, entity: schema.Server) -> Mobject:
        return self.with_time(style.actor("Temporal Server"), entity)

    @staticmethod
    def get_child_entities(entity: schema.Server) -> list[schema.History]:
        try:
            [shard] = entity.shards
        except ValueError:
            raise ValueError("Multiple history shards are not supported")
        try:
            [namespace] = shard.values()
        except ValueError:
            raise ValueError("Multiple namespaces are not supported")
        return [w.history for w in namespace.values()]

    def get_message_end(self, message_entity: schema.RequestResponse) -> Point3D:
        if isinstance(message_entity, schema.WorkerPollRequest):
            return self.mobj.get_center()
        else:
            return super().get_message_end(message_entity)
