import asyncio
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Coroutine, Iterable, List, Tuple, Type

from manim import DL, DOWN, LEFT, ORIGIN, RIGHT, UL, UP, UR, Dot, Scene, Text

from tempyral import animation
from tempyral.simulation import (
    ActivityWorker,
    Application,
    Entity,
    Server,
    WorkflowWorker,
)


class TemporalScene(Scene, ABC):
    """
    To create an animation, subclass TemporalScene and implement `simulation()`.
    """

    workflow_worker_cls: Type[WorkflowWorker]

    @abstractmethod
    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: WorkflowWorker,
        activity_worker: ActivityWorker,
    ) -> Iterable[Coroutine]:
        ...

    def construct(self):
        self.add_timestamp()
        server, apps, wworkers, aworkers = self.make_simulation_entities()
        self.make_animation_proxies(server, apps, wworkers, aworkers)

    async def do_simulation(
        self,
        server: Server,
        apps: List[Application],
        workflow_workers: List[WorkflowWorker],
        activity_workers: List[ActivityWorker],
        render: bool,
    ):
        [app] = apps
        [wworker] = workflow_workers
        [aworker] = activity_workers
        try:
            async with asyncio.TaskGroup() as tg:
                simulation_tasks = [
                    tg.create_task(coro)
                    for coro in self.simulation(server, app, wworker, aworker)
                ]

                if render:
                    simulation_tasks.append(
                        tg.create_task(animation.process_simulation_events(self))
                    )

                def cancel(_):
                    for t in simulation_tasks:
                        t.cancel()

                Entity.terminate_simulation = cancel

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
            [Application()],
            [self.workflow_worker_cls(server)],
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

        server.set_dock_direction(LEFT).m.align_on_border(UR).shift(3 * DOWN)
        app.set_dock_direction(RIGHT).m.align_on_border(UL)
        aworker.set_dock_direction(RIGHT).m.next_to(app.m, DOWN).shift(1 * DOWN)
        wworker.set_dock_direction(RIGHT).m.next_to(aworker.m, DOWN).align_to(
            server.m, UP
        )

        self.add(app.m, server.m, wworker.m, aworker.m)

        for a, s in zip(
            [server, *[app], *[wworker]],
            [simulation_server, *simulation_apps, *simulation_workflow_workers],
        ):
            a.render(s)  # type:ignore

        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=24)
        time.to_corner(DL, buff=0.1)
        self.add(time)

    def add_dock_points(
        self,
        server: animation.Server,
        app: animation.Application,
        wworker: animation.WorkflowWorker,
    ):
        self.add(*(Dot().move_to(e.dock_point()) for e in [server, app, wworker]))
