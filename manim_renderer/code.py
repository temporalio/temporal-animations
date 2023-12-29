from typing import Generic, TypeVar

from manim import BLACK, DOWN, LEFT, PINK, Arrow, Code, Mobject, VGroup

import tempyral
from manim_renderer.entity import ProxyEntity
from manim_renderer.mobject import FONT_SIZE_CODE

E = TypeVar("E", bound=tempyral.EntityWithCode)


class ProxyEntityWithCode(ProxyEntity, Generic[E]):
    def render(self, entity: E) -> Mobject:
        code = Code(
            code=entity.code,
            language=entity.language,
            insert_line_no=False,
            font_size=FONT_SIZE_CODE,
            line_spacing=0.3,
        ).to_edge(LEFT, buff=0.1)
        lines = code[2]
        arrows = VGroup(
            *(
                Arrow(
                    start=line.get_edge_center(LEFT) + LEFT,
                    end=line.get_edge_center(LEFT),
                    color=BLACK,
                )
                .next_to(line, LEFT, buff=0.1)
                .shift(DOWN * 0.025)
                for line in lines
            )
        )
        for line_num in entity.blocked_expressions:
            arrows[line_num - 1].set_color(PINK)
        return VGroup(code, arrows)
