import asyncio
from datetime import datetime
from typing import Coroutine, List, Tuple

from manim import DOWN, LEFT, ORIGIN, RIGHT, UL, UP, Scene, Text

from tempyral import animation
from tempyral.event_bus import EventBus
from tempyral.simulation import Application, Server, WorkflowWorker

TIMEOUT_SECONDS = 10


class ExecuteWorkflow(Scene):
    async def simulation(
        self,
        server: Server,
        apps: List[Application],
        workflow_workers: List[WorkflowWorker],
    ):
        [app], [wworker] = apps, workflow_workers
        async with asyncio.TaskGroup() as tg:
            tg.create_task(wworker.poll(server))
            tg.create_task(app.start_workflow(server))

    def construct(self):
        self.add_timestamp()
        server, [app], [wworker] = self.make_simulation_entities()
        self.make_animation_entities(server, [app], [wworker])

        async def simulation():
            try:
                async with asyncio.timeout(TIMEOUT_SECONDS):
                    await self.simulation(server, [app], [wworker])
            except TimeoutError:
                pass

        asyncio.run(simulation())
        self.wait(2)

    def make_simulation_entities(
        self,
    ) -> Tuple[Server, List[Application], List[WorkflowWorker]]:
        event_bus: EventBus[animation.VisualElement] = EventBus()

        server = Server(event_bus, proxy=animation_server)
        app = Application(event_bus, proxy=animation_app)
        wworker = WorkflowWorker(event_bus, proxy=animation_wworker)

        return server, [app], [wworker]

    def make_animation_entities(
        self,
        simulation_server: Server,
        simulation_apps: List[Application],
        simulation_workflow_workers: List[WorkflowWorker],
    ):
        """
        Create entities in the animation domain, adding them to the scene.

        The animation entities have references to their simulation counterparts.
        """
        server = animation.Server(self, simulation_server)
        [app] = [
            animation.Application(self, simulation_app)
            for simulation_app in simulation_apps
        ]
        [wworker] = [
            animation.WorkflowWorker(self, simulation_workflow_worker)
            for simulation_workflow_worker in simulation_workflow_workers
        ]

        server.m.move_to(ORIGIN + UP * 2)
        app.m.move_to(ORIGIN + LEFT * 3 + DOWN * 2)
        wworker.m.move_to(ORIGIN + RIGHT * 3 + DOWN * 2)

        self.add(app.m, server.m, wworker.m)
        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=24)
        time.to_corner(UL, buff=0.1)
        self.add(time)
