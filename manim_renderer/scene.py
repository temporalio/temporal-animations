import asyncio
import os
import sys
import traceback
from datetime import datetime
from typing import Coroutine, List, Tuple, Type

from manim import (
    DL,
    DOWN,
    LEFT,
    RIGHT,
    SMALL_BUFF,
    UP,
    Camera,
    Dot,
    Scene,
    Text,
    config,
)

import manim_renderer as renderer
from manim_renderer.style import COLOR_SCENE_BACKGROUND
from manim_renderer.utils import debug
from tempyral import (
    ActivityWorker,
    Application,
    Entity,
    Server,
    Workflow,
    WorkflowWorker,
)

if os.getenv("MANIM_DRY_RUN"):
    config.dry_run = True


class TemporalScene(Scene):
    """
    To create an animation:

    - create a subclass of this class
    - set the `workflow_classes` class attribute
    - implement `simulation()`
    """

    application_classes: List[Type[Application]]
    workflow_classes: List[Type[Workflow]]

    def setup(self):
        assert isinstance(self.camera, Camera)
        self.camera.background_color = COLOR_SCENE_BACKGROUND

    def construct(self):
        self.add_timestamp()
        server, apps, wworkers, aworkers = self.make_simulation_entities()
        self.make_renderer_proxies(server, apps, wworkers, aworkers)
        asyncio.run(self.do_simulation(server, apps, wworkers, aworkers, render=True))
        self.wait(2)

    async def do_simulation(
        self,
        server: Server,
        apps: List[Application],
        workflow_workers: List[WorkflowWorker],
        activity_workers: List[ActivityWorker],
        render: bool,
    ):
        coros: List[Coroutine] = [
            debug(w.poll(server)) for w in workflow_workers + activity_workers
        ]
        for app in apps:
            coros.extend(map(debug, app.get_coroutines(server)))
        if render:
            coros.append(debug(renderer.process_simulation_events()))

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(coro) for coro in coros]
                Entity.terminate_simulation = lambda _: [t.cancel() for t in tasks]

        except ExceptionGroup as eg:
            print(f"Caught ExceptionGroup:", file=sys.stderr)
            for e in eg.exceptions:
                print(f"    {e}", file=sys.stderr)
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            sys.exit(1)

    def make_simulation_entities(
        self,
    ) -> Tuple[Server, List[Application], List[WorkflowWorker], List[ActivityWorker]]:
        server = Server()

        return (
            server,
            [cls() for cls in self.application_classes],
            [WorkflowWorker(self.workflow_classes)],
            [ActivityWorker()],
        )

    def make_renderer_proxies(
        self,
        simulation_server: Server,
        simulation_apps: List[Application],
        simulation_workflow_workers: List[WorkflowWorker],
        simulation_activity_workers: List[ActivityWorker],
    ):
        """
        Create proxy entities and add them to the manim scene.
        """
        renderer.set_scene(self)
        server = renderer.Server(simulation_server.clone())
        [app] = [renderer.Application(a.clone()) for a in simulation_apps]
        [wworker] = [
            renderer.WorkflowWorker(w.clone()) for w in simulation_workflow_workers
        ]
        [aworker] = [
            renderer.ActivityWorker(w.clone()) for w in simulation_activity_workers
        ]

        app.set_dock_direction(RIGHT).mobj.align_on_border(
            UP, buff=0.25
        ).align_on_border(LEFT, buff=SMALL_BUFF)
        wworker.set_dock_direction(RIGHT).mobj.next_to(app.mobj, DOWN).align_to(
            app.mobj, LEFT
        ).shift(DOWN * 0.5)
        aworker.set_dock_direction(RIGHT).mobj.next_to(
            wworker.children[-1].mobj, DOWN
        ).align_to(wworker.mobj, LEFT).shift(DOWN)
        server.set_dock_direction(UP).mobj.align_on_border(RIGHT).align_to(
            wworker.mobj, UP
        ).shift(1.5 * LEFT)

        self.add(app.mobj, server.mobj, wworker.mobj, aworker.mobj)

        if False:
            self.add(
                *(
                    Dot(radius=0.02).move_to(t.dock_point())
                    for t in [app, server, wworker, aworker]
                )
            )

        for a, s in zip(
            [server, *[app], *[wworker]],
            [simulation_server, *simulation_apps, *simulation_workflow_workers],
        ):
            a.render_to_scene(s.clone())  # type: ignore

        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=8)
        time.to_corner(DL, buff=0.1)
        self.add(time)

    def add_dock_points(
        self,
        server: renderer.Server,
        app: renderer.Application,
        wworker: renderer.WorkflowWorker,
    ):
        self.add(*(Dot().move_to(e.dock_point()) for e in [server, app, wworker]))


def run_simulation(scene: TemporalScene):
    asyncio.run(scene.do_simulation(*scene.make_simulation_entities(), render=False))
