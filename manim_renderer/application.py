from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VGroup
from manim.typing import Point3D

import tempyral
from manim_renderer import style
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import ProxyEntity


class ApplicationRequest(ProxyEntity[tempyral.ApplicationRequest]):
    def render(self, entity: tempyral.ApplicationRequest) -> Mobject:
        return self.with_time(style.message(entity.request_type.name), entity)


class Application(ProxyEntityWithCode[tempyral.Application]):
    """
    An Application has code, like a WorkflowWorker. But whereas the code of a
    WorkflowWorker is associated with child Workflows objects, the code of an
    Application is part of the self.mobj VGroup.
    """

    def render(self, entity: tempyral.Application) -> Mobject:
        code = super().render(entity)
        text = self.with_time(style.actor("Your Application"), entity)
        return VGroup(text, code).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)

    def dock_point(self) -> Point3D:
        return (
            self.mobj[0].get_edge_center(self.dock_direction)
            + 0.5 * self.dock_direction
        )
