from manim import DOWN, LEFT, SMALL_BUFF, Mobject, Text, VGroup

from tempyral import simulation
from tempyral.animation.code import ProxyEntityWithCode
from tempyral.animation.entity import FONT_SIZE_MEDIUM, MONOSPACE_FONT, VisualElement


class ApplicationRequest(VisualElement):
    @staticmethod
    def newm(request: simulation.ApplicationRequest) -> Mobject:
        return Text(
            request.request_type.name, font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT
        )


class Application(ProxyEntityWithCode[simulation.Application]):
    def newm(self, entity: simulation.Application) -> Mobject:
        code = super().newm(entity)
        text = Text("Application", font_size=24)
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
