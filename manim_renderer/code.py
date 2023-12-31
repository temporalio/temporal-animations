from typing import Generic, TypeVar

from manim import DOWN, LEFT, PINK, Arrow, Code, Mobject, VGroup

import tempyral
from manim_renderer.entity import ProxyEntity
from manim_renderer.mobject import FONT_CODE, FONT_SIZE_CODE

E = TypeVar("E", bound=tempyral.EntityWithCode)


class ProxyEntityWithCode(ProxyEntity, Generic[E]):
    def render(self, entity: E) -> Mobject:
        code = Code(
            code=entity.code,
            language=entity.language,
            insert_line_no=False,
            background_stroke_width=1,
            font_size=FONT_SIZE_CODE,
            font=FONT_CODE,
            line_spacing=0.7,
        ).to_edge(LEFT, buff=0.1)
        lines = code[2]
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
        for line_num in entity.blocked_expressions:
            arrows[line_num - 1].set_color(PINK).set_opacity(1)
        return VGroup(code, arrows)
