from manim import Mobject, Text

from tempyral import simulation
from tempyral.animation.entity import (
    FONT_SIZE_MEDIUM,
    MONOSPACE_FONT,
    ProxyEntity,
    VisualElement,
)


class ApplicationRequest(VisualElement):
    @staticmethod
    def newm(request: simulation.ApplicationRequest) -> Mobject:
        return Text(
            request.request_type.name, font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT
        )


class Application(ProxyEntity[simulation.Application]):
    @staticmethod
    def newm(_: simulation.Application) -> Mobject:
        return Text("Application", font_size=24)
