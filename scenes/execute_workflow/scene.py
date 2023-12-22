import asyncio
from datetime import datetime
from typing import Coroutine, List, Tuple

from manim import DOWN, LEFT, ORIGIN, RIGHT, UL, UP, Scene, Text

from tempyral.entity import Application, Server, WorkflowWorker
from tempyral.event_bus import event_bus

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
        server, [app], [wworker] = self.make_temporal_entities()
        self.add(app.m, server.m, wworker.m)

        async def simulation():
            try:
                async with asyncio.timeout(TIMEOUT_SECONDS):
                    await self.simulation(server, [app], [wworker])
            except TimeoutError:
                pass

        asyncio.run(simulation())
        self.wait(2)

    def make_temporal_entities(
        self,
    ) -> Tuple[Server, List[Application], List[WorkflowWorker]]:
        server = Server(event_bus)
        app = Application(event_bus)
        wworker = WorkflowWorker(event_bus)

        server.m.move_to(ORIGIN + UP * 2)
        app.m.move_to(ORIGIN + LEFT * 3 + DOWN * 2)
        wworker.m.move_to(ORIGIN + RIGHT * 3 + DOWN * 2)

        return server, [app], [wworker]

    def add_timestamp(self):
        time = Text(datetime.now().strftime("%H:%M:%S"), font_size=24)
        time.to_corner(UL, buff=0.1)
        self.add(time)
