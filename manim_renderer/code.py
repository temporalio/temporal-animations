from typing import Generic, TypeVar

from manim import DOWN, LEFT, PINK, Arrow, VDict, VGroup, VMobject

from manim_renderer.entity import ProxyEntity
from manim_renderer.manim_shims import Code
from schema import schema

E = TypeVar("E", bound=schema.EntityWithCode)


class ProxyEntityWithCode(ProxyEntity, Generic[E]):
    CODE_LINES_INDEX = 2

    def render(self, entity: E) -> VMobject:
        code = Code(
            code=entity.code,
            language=entity.language,
            insert_line_no=False,
            background_stroke_width=1,
            background_stroke_color=str(
                style.COLOR_ACTIVE_CODE if entity.active else style.COLOR_INACTIVE_CODE
            ),
            font_size=style.FONT_SIZE_CODE,
            font=style.FONT_CODE,
            line_spacing=0.5,
        ).to_edge(LEFT, buff=0.1)
        lines = code[self.CODE_LINES_INDEX]
        arrows = VGroup(
            *(
                Arrow(
                    start=line.get_edge_center(LEFT) + LEFT,
                    end=line.get_edge_center(LEFT),
                )
                .set_opacity(0)
                .next_to(line, LEFT, buff=0.1)
                .shift(DOWN * 0.025)
                for line in lines
            )
        )
        for line_num in entity.blocked_lines:
            arrows[line_num - 1].set_color(PINK).set_opacity(1)
        return VDict({"code": code, "arrows": arrows})
