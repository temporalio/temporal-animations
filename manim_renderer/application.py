from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import Message, MessageStage, VisualElement


class ApplicationRequest(Message):
    message_stage = MessageStage.Request

    def render(self, request: tempyral.ApplicationRequest) -> Mobject:
        return mobject.message(request.request_type.name)


class ApplicationResponse(Message):
    message_stage = MessageStage.Response

    def render(self, response: tempyral.ApplicationResponse) -> Mobject:
        return mobject.message(response.request.request_type.name)


class Application(ProxyEntityWithCode[tempyral.Application]):
    def render(self, entity: tempyral.Application) -> Mobject:
        code = super().render(entity)
        text = mobject.actor("Application")
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
