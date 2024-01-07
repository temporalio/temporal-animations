from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VDict
from manim.typing import Point3D

from manim_renderer import style
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import ProxyEntity
from schema import schema


class ApplicationRequest(ProxyEntity[schema.ApplicationRequest]):
    def render(self, entity: schema.ApplicationRequest) -> Mobject:
        match entity.stage:
            case schema.RequestResponseStage.Response if entity.response_payload:
                label = str(entity.response_payload)
            case _:
                label = entity.request_type.name
        return self.with_time(style.message(label), entity)


class Application(ProxyEntityWithCode[schema.Application]):
    """
    An Application has code, like a WorkflowWorker. But whereas the code of a
    WorkflowWorker is associated with child Workflows objects, the code of an
    Application is part of the self.mobj VGroup.
    """

    def render(self, entity: schema.Application) -> Mobject:
        code = super().render(entity)
        text = self.with_time(style.actor("Your Application"), entity)
        return VDict({"text": text, "code": code}).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )

    def dock_point(self) -> Point3D:
        return (
            self.mobj["text"].get_edge_center(self.dock_direction)
            + 0.5 * self.dock_direction
        )

    def get_message_start(self, message_entity: schema.RequestResponse) -> Point3D:
        if (line_num := message_entity.token) is not None:
            return self.mobj["code"]["code"][self.CODE_LINES_INDEX][
                line_num - 1
            ].get_center()
        else:
            return super().get_message_start(message_entity)
