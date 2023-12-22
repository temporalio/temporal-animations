from manim import DOWN, LEFT, ORIGIN, RIGHT, UP, Create, Scene

from tempyral.manim_entity import Application, Server, WorkflowWorker


class ExecuteWorkflow(Scene):
    def construct(self):
        server = Server(self)
        app = Application(self)
        wworker = WorkflowWorker(self)

        server.m.move_to(ORIGIN + UP * 2)
        app.m.move_to(ORIGIN + LEFT * 3 + DOWN * 2)
        wworker.m.move_to(ORIGIN + RIGHT * 3 + DOWN * 2)

        self.add(app.m, server.m, wworker.m)
        self.play(*(Create(s.m) for s in [app, server, wworker]))

        self.wait()

        for i in range(4):
            if i == 2:
                app.start_workflow(server)
            server.dispatch_wft(wworker)

        self.wait(2)
