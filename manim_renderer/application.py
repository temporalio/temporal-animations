from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.message import ProxyEntityRequestMessage, ProxyEntityResponseMessage


class ApplicationRequest(ProxyEntityRequestMessage[tempyral.ApplicationRequest]):
    def render(self, entity: tempyral.ApplicationRequest) -> Mobject:
        return mobject.message(entity.request_type.name)


class ApplicationResponse(ProxyEntityResponseMessage[tempyral.ApplicationResponse]):
    def render(self, entity: tempyral.ApplicationResponse) -> Mobject:
        return mobject.message(entity.request.request_type.name)


class Application(ProxyEntityWithCode[tempyral.Application]):
    def render(self, entity: tempyral.Application) -> Mobject:
        code = super().render(entity)
        text = mobject.actor("Application")
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
