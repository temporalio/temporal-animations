from typing import Self, cast

import manim

from manim_renderer.style import COLOR_SCENE_BACKGROUND


class _NotNone:
    # manim.Animation.__new__ has a code path allowing None to be returned,
    # and type-checkers infer its return type to be Self | None.
    def __new__(cls, *args, **kwargs) -> Self:
        return cast(Self, super().__new__(cls, *args, **kwargs))


class ApplyMethod(_NotNone, manim.ApplyMethod):
    pass


class AnimationGroup(_NotNone, manim.AnimationGroup):
    pass


class Transform(_NotNone, manim.Transform):
    pass


class Code(manim.Code):
    # Code doesn't make it easy to set background color.
    @property
    def background_color(self):
        return COLOR_SCENE_BACKGROUND

    @background_color.setter
    def background_color(self, _):
        pass
