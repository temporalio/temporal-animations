from manim import Mobject, Text

from manim_renderer.entity import ProxyEntity
from schema import schema


class NexusServer(ProxyEntity[schema.NexusServer]):
    def render(self, _: schema.NexusServer) -> Mobject:
        return Text("Nexus Server")


class NexusWorker(ProxyEntity[schema.NexusWorker]):
    def render(self, _: schema.NexusWorker) -> Mobject:
        return Text("Nexus Worker")
