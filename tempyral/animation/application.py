from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VGroup

from tempyral import simulation
from tempyral.animation import mobject
from tempyral.animation.code import ProxyEntityWithCode
from tempyral.animation.entity import VisualElement


class ApplicationRequest(VisualElement):
    def newm(self, request: simulation.ApplicationRequest) -> Mobject:
        return mobject.message(request.request_type.name)


class Application(ProxyEntityWithCode[simulation.Application]):
    def newm(self, entity: simulation.Application) -> Mobject:
        code = super().newm(entity)
        text = mobject.actor("Application")
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
