from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.message import ProxyEntityRequestMessage


class ApplicationRequest(ProxyEntityRequestMessage[tempyral.ApplicationRequest]):
    def render(self, entity: tempyral.ApplicationRequest) -> Mobject:
        return self.with_time(mobject.message(entity.request_type.name), entity)


class Application(ProxyEntityWithCode[tempyral.Application]):
    def render(self, entity: tempyral.Application) -> Mobject:
        code = super().render(entity)
        text = self.with_time(mobject.actor("Your Application"), entity)
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
