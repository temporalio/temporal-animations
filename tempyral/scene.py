import asyncio
import sys
import traceback
from datetime import datetime
from typing import Coroutine, List, Tuple, Type

from manim import (
    DL,
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    SMALL_BUFF,
    UL,
    UP,
    UR,
    Dot,
    Scene,
    Text,
)

from tempyral import animation
from tempyral.simulation import (
    ActivityWorker,
    Application,
    Entity,
    Server,
    Worker,
    Workflow,
    WorkflowWorker,
)


class TemporalScene(Scene):
    """
    To create an animation:

    - create a subclass of this class
    - set the `workflow_classes` class attribute
    - implement `simulation()`
    """

    application_classes: List[Type[Application]]
    workflow_classes: List[Type[Workflow]]

    def construct(self):
        self.add_timestamp()
        server, apps, wworkers, aworkers = self.make_simulation_entities()
        self.make_animation_proxies(server, apps, wworkers, aworkers)
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
            worker.poll(server) for worker in workflow_workers + activity_workers
        ]
        for app in apps:
            coros.extend(app.get_coroutines(server))
        if render:
            coros.append(animation.process_simulation_events())

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
            [WorkflowWorker(self.workflow_classes, server)],
            [ActivityWorker(server)],
        )

    def make_animation_proxies(
        self,
        simulation_server: Server,
        simulation_apps: List[Application],
        simulation_workflow_workers: List[WorkflowWorker],
        simulation_activity_workers: List[ActivityWorker],
    ):
        """
        Create proxy entities in the animation domain, adding them to the scene.
        """
        animation.set_scene(self)
        server = animation.Server(simulation_server)
        [app] = [
            animation.Application(simulation_app) for simulation_app in simulation_apps
        ]
        [wworker] = [
            animation.WorkflowWorker(sim_wworker)
            for sim_wworker in simulation_workflow_workers
        ]
        [aworker] = [
            animation.ActivityWorker(sim_aworker)
            for sim_aworker in simulation_activity_workers
        ]

        app.set_dock_direction(RIGHT).mobj.align_on_border(UP).align_on_border(
            LEFT, buff=SMALL_BUFF
        )
        aworker.set_dock_direction(RIGHT).mobj.next_to(app.mobj, DOWN).align_to(
            app.mobj, LEFT
        ).shift(DOWN)
        wworker.set_dock_direction(RIGHT).mobj.next_to(aworker.mobj, DOWN).align_to(
            aworker.mobj, LEFT
        ).shift(DOWN)
        server.set_dock_direction(LEFT).mobj.align_on_border(RIGHT).align_to(
            aworker.mobj, UP
        ).shift(1.5 * LEFT)

        self.add(app.mobj, server.mobj, wworker.mobj, aworker.mobj)

        for a, s in zip(
            [server, *[app], *[wworker]],
            [simulation_server, *simulation_apps, *simulation_workflow_workers],
        ):
            a.update(s)  # type:ignore

        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=8)
        time.to_corner(DL, buff=0.1)
        self.add(time)

    def add_dock_points(
        self,
        server: animation.Server,
        app: animation.Application,
        wworker: animation.WorkflowWorker,
    ):
        self.add(*(Dot().move_to(e.dock_point()) for e in [server, app, wworker]))


def run_simulation(scene: TemporalScene):
    asyncio.run(scene.do_simulation(*scene.make_simulation_entities(), render=False))
