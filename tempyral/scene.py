import asyncio
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Coroutine, Iterable, List, Tuple

from manim import DL, DOWN, LEFT, ORIGIN, RIGHT, UL, UP, UR, Dot, Scene, Text

from tempyral import animation
from tempyral.simulation import Application
from tempyral.simulation import NoOpWorkflowWorker as WorkflowWorker
from tempyral.simulation import Server


class TemporalScene(Scene, ABC):
    """
    To create an animation, subclass TemporalScene and implement `simulation()`.
    """

    @abstractmethod
    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: WorkflowWorker,
    ) -> Iterable[Coroutine]:
        ...

    def construct(self):
        self.add_timestamp()
        server, [app], [wworker] = self.make_simulation_entities()
        self.make_animation_proxies(server, [app], [wworker])

        async def simulation():
            try:
                async with asyncio.TaskGroup() as tg:
                    simulation_tasks = [
                        tg.create_task(coro)
                        for coro in self.simulation(server, app, wworker)
                    ]
                    animation_task = tg.create_task(
                        animation.process_simulation_events(self)
                    )

                    # The animation task terminates when the workflow is
                    # complete. When this happens, cancel the simulation tasks
                    # (e.g. worker polling).
                    def cancel(_):
                        for t in simulation_tasks:
                            t.cancel()

                    animation_task.add_done_callback(cancel)
            except ExceptionGroup as eg:
                print(f"Caught ExceptionGroup:", file=sys.stderr)
                for e in eg.exceptions:
                    print(f"    {e}", file=sys.stderr)
                    traceback.print_exception(
                        type(e), e, e.__traceback__, file=sys.stderr
                    )
                sys.exit(1)

        self.wait()
        asyncio.run(simulation())
        self.wait(2)

    def make_simulation_entities(
        self,
    ) -> Tuple[Server, List[Application], List[WorkflowWorker]]:
        return Server(), [Application()], [WorkflowWorker()]

    def make_animation_proxies(
        self,
        simulation_server: Server,
        simulation_apps: List[Application],
        simulation_workflow_workers: List[WorkflowWorker],
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

        server.m.move_to(ORIGIN + UP * 2)
        app.m.move_to(ORIGIN + LEFT * 3 + DOWN * 2)
        wworker.m.move_to(ORIGIN + RIGHT * 3 + DOWN * 2)

        server.dock_direction = DOWN
        app.dock_direction = UL
        wworker.dock_direction = UR
        self.add(*(Dot().move_to(e.dock_point()) for e in [server, app, wworker]))

        self.add(app.m, server.m, wworker.m)
        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=24)
        time.to_corner(DL, buff=0.1)
        self.add(time)
