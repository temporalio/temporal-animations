from typing import Generic, TypeVar

from manim import BLACK, DOWN, LEFT, PINK, Arrow, Code, Mobject, VGroup

from tempyral import simulation
from tempyral.animation.entity import FONT_SIZE_SMALL, ProxyEntity

E = TypeVar("E", bound=simulation.EntityWithCode)


class ProxyEntityWithCode(ProxyEntity, Generic[E]):
    def newm(self, entity: E) -> Mobject:
        code = Code(
            code=entity.code,
            language=entity.language,
            insert_line_no=False,
            font_size=FONT_SIZE_SMALL,
            line_spacing=1,
            background_stroke_width=0,
        ).to_edge(LEFT, buff=1.0)
        lines = code[2]
        arrows = VGroup(
            *(
                Arrow(
                    start=line.get_edge_center(LEFT) + LEFT,
                    end=line.get_edge_center(LEFT),
                    color=BLACK,
                )
                .next_to(line, LEFT, buff=0.1)
                .shift(DOWN * 0.075)
                for line in lines
            )
        )
        for line_num in entity.blocked_expressions:
            arrows[line_num - 1].set_color(PINK)
        return VGroup(code, arrows)
