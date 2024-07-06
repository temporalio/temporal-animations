from dataclasses import dataclass
from itertools import chain
from typing import Iterable

import esv
from manim import LEFT, Camera, Create, VGroup, VMobject

from manim_renderer import style
from scenes.worker.constants import CONTAINER_HEIGHT, CONTAINER_WIDTH
from scenes.worker.coroutines import Coroutines
from scenes.worker.history import HistoryEvent
from scenes.worker.input import commands, history
from scenes.worker.scheduler import Scheduler
from scenes.worker.state_machines import WorkflowStateMachines
from scenes.worker.utils import label_text


@dataclass
class Event(esv.Event):
    history_event: HistoryEvent


class WorkerScene(esv.Scene):
    def events(self) -> Iterable[esv.Event]:
        return (Event(e) for e in history.unapplied_events)

    def handle(self, event: Event):
        history_event = event.history_event
        self.state_machines.handle_event(history_event)
        history_event.seen_by_worker = True
        history.applied_events.append(history_event)
        self.unapplied_events_mobj.become(history.render_unapplied())
        self.applied_events_mobj.become(history.render_applied())
        self.wait(2)

    def init(self) -> None:
        assert isinstance(self.camera, Camera)
        self.camera.background_color = style.COLOR_SCENE_BACKGROUND

        self.coroutines = Coroutines("coroutines")
        self.scheduler = Scheduler("scheduler", coroutines=self.coroutines)
        self.state_machines = WorkflowStateMachines(
            "WorkflowStateMachines",
            scheduler=self.scheduler,
            user_workflow_code=iter(commands),
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

        self.unapplied_events_mobj = history.render_unapplied()
        self.applied_events_mobj = history.render_applied()
        self.add(self.unapplied_events_mobj)
        self.add(self.applied_events_mobj)
        self.wait(2)
        self.entities = {
            "coroutines": self.coroutines,
            "scheduler": self.scheduler,
            "state_machines": self.state_machines,
        }
