import json
import os
import sys
from datetime import datetime
from typing import Iterator, cast

from manim import DL, DOWN, LEFT, RIGHT, SMALL_BUFF, UP, Camera, Dot, Scene, Text

import manim_renderer as renderer
from manim_renderer.style import COLOR_SCENE_BACKGROUND
from schema import schema


class TemporalScene(Scene):
    app: renderer.Application
    server: renderer.Server
    workflow_worker: renderer.WorkflowWorker
    activity_worker: renderer.ActivityWorker | None

    def construct(self):
        events = read_events()
        match event := next(events):
            case schema.NexusInitEvent():
                self.init_nexus(event)
            case schema.InitEvent():
                self.init(event)
            case _:
                raise ValueError("The first event must be an InitEvent")
        renderer.render_simulation_events(events)
        self.wait(2)

    def init(
        self,
        event: schema.InitEvent,
    ):
        """
        Initialize the manim scene.
        """
        renderer.set_scene(self)
        assert isinstance(self.camera, Camera)
        self.camera.background_color = COLOR_SCENE_BACKGROUND
        self.add_timestamp()

        server = renderer.Server(event.server)
        [app] = [renderer.Application(a) for a in event.apps]
        [wworker] = [renderer.WorkflowWorker(w) for w in event.workflow_workers]
        aworkers = [renderer.ActivityWorker(w) for w in event.activity_workers]

        app.set_dock_direction(RIGHT).mobj.align_on_border(
            UP, buff=0.25
        ).align_on_border(LEFT, buff=SMALL_BUFF)
        wworker.set_dock_direction(RIGHT).mobj.next_to(app.mobj, DOWN).align_to(
            app.mobj, LEFT
        ).shift(DOWN * 0.2)
        server.set_dock_direction(UP).mobj.align_on_border(RIGHT).align_to(
            wworker.mobj, UP
        ).shift(1.5 * LEFT)
        if aworkers:
            [aworker] = aworkers
            aworker.set_dock_direction(RIGHT).mobj.next_to(
                wworker.children[-1].mobj, DOWN
            ).align_to(wworker.mobj, LEFT).shift(DOWN * 0.5)
        else:
            aworker = None

        self.add(app.mobj, server.mobj, wworker.mobj, *(a.mobj for a in aworkers))

        for a, s in zip(
            [server, *[app], *[wworker]],
            [event.server, *event.apps, *event.workflow_workers],
        ):
            a.render_to_scene(s)  # type: ignore

        self.app = app
        self.server = server
        self.workflow_worker = wworker
        self.activity_worker = aworker

    def init_nexus(self, event: schema.NexusInitEvent):
        self.init(event)
        nexus_server = renderer.NexusServer(event.nexus_server)
        [nexus_worker] = [renderer.NexusWorker(w) for w in event.nexus_workers]

        self.workflow_worker.mobj.shift(DOWN * 3)
        for c in self.workflow_worker.children:
            c.mobj.shift(DOWN * 3)

        nexus_server.set_dock_direction(DL).mobj.next_to(self.server.mobj, UP).align_to(
            self.server.mobj, LEFT
        )
        nexus_worker.set_dock_direction(RIGHT).mobj.next_to(
            self.app.mobj, DOWN
        ).align_to(self.app.mobj, LEFT)

        self.add(nexus_server.mobj, nexus_worker.mobj)

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=8)
        time.to_corner(DL, buff=0.1)
        self.add(time)

    def add_dock_point(self, entity: renderer.ProxyEntity):
        self.add(Dot().move_to(entity.dock_point()))


def read_events() -> Iterator[schema.Event]:
    if events_file := os.getenv("TEMPORAL_ANIMATIONS_EVENTS_FILE"):
        file = open(events_file)
    else:
        file = sys.stdin
    for line in file.readlines():
        data = json.loads(line)
        yield cast(schema.Event, schema.from_serializable(data))
