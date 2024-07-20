from itertools import chain
from typing import Iterable

from manim import LEFT, Camera, Create, VGroup, VMobject

import esv
from scenes.worker import input, style
from scenes.worker.constants import CONTAINER_HEIGHT, CONTAINER_WIDTH
from scenes.worker.coroutines import Coroutines
from scenes.worker.history import History
from scenes.worker.scheduler import Scheduler
from scenes.worker.state_machines import WorkflowStateMachines
from scenes.worker.utils import label_text


class WorkerScene(esv.Scene):
    def events(self) -> Iterable[input.Event]:
        return (input.Event(h) for h in self.history.events)

    def init(self) -> None:
        assert isinstance(self.camera, Camera)
        self.camera.background_color = style.COLOR_SCENE_BACKGROUND

        self.coroutines = Coroutines()
        self.scheduler = Scheduler(coroutines=self.coroutines)
        self.state_machines = WorkflowStateMachines(
            scheduler=self.scheduler,
            user_workflow_code=iter(input.commands),
        )

        # Main layout is a grid. The left column contains labels, and the right
        # column contains a stage area for entities of the type corresponding to
        # the row label.
        h, w = CONTAINER_HEIGHT, CONTAINER_WIDTH
        rows = [
            (VMobject(), self.scheduler.mobj),
            (label_text("Coroutines"), self.coroutines.mobj),
            (label_text("State machines"), self.state_machines.mobj),
        ]
        grid = (
            VGroup(*chain.from_iterable(rows))
            .arrange_in_grid(
                cols=2,
                col_widths=[None, w],
                row_heights=[0.5, h, h],
                buff=0.5,
            )
            .align_on_border(LEFT)
        )
        self.play(Create(grid))

        self.history = History(events=input.history_events)
        self.add(self.history.mobj)
        self.entities: dict[str, esv.Entity] = {
            "history": self.history,
            "coroutines": self.coroutines,
            "scheduler": self.scheduler,
            "state_machines": self.state_machines,
        }
        self.wait(2)
