from datetime import datetime
from typing import Tuple

from manim import DOWN, LEFT, ORIGIN, RIGHT, UL, UP, Scene, Text

from tempyral.manim_entity import Application, Server, WorkflowWorker


class ExecuteWorkflow(Scene):
    def construct(self):
        self.add_timestamp()
        server, app, wworker = self.make_temporal_entities()
        self.add(app.m, server.m, wworker.m)

        for i in range(2):
            if i == 1:
                app.start_workflow(server)
            server.maybe_dispatch_wft(wworker)

        self.wait(2)

    def make_temporal_entities(self) -> Tuple[Server, Application, WorkflowWorker]:
        server = Server(self)
        app = Application(self)
        wworker = WorkflowWorker(self)

        server.m.move_to(ORIGIN + UP * 2)
        app.m.move_to(ORIGIN + LEFT * 3 + DOWN * 2)
        wworker.m.move_to(ORIGIN + RIGHT * 3 + DOWN * 2)

        return server, app, wworker

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=24)
        time.to_corner(UL, buff=0.1)
        self.add(time)
