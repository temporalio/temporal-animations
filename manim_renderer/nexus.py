from manim import Mobject

from manim_renderer import style
from manim_renderer.entity import ProxyEntity
from schema import schema


class NexusServer(ProxyEntity[schema.NexusServer]):
    def render(self, _: schema.NexusServer) -> Mobject:
        return style.actor("Nexus Server")


class NexusWorker(ProxyEntity[schema.NexusWorker]):
    def render(self, _: schema.NexusWorker) -> Mobject:
        return style.actor("Nexus Worker")
