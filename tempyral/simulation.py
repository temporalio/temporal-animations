import asyncio
import sys
import traceback
from typing import Coroutine, Type

from tempyral.application import AbstractApplication
from tempyral.entity import Entity
from tempyral.event import emit_init_event
from tempyral.server import Server
from tempyral.worker import ActivityWorker, Workflow, WorkflowWorker


class Simulation:
    # A simulation specifies its own application classes
    application_classes: list[Type[AbstractApplication]]
    # A simulation specifies its own workflows; a single workflow worker is
    # created to execute them
    workflow_classes: list[Type[Workflow]]
    # A simulation may optionally specify an activity worker.
    activity_worker_classes: list[Type[ActivityWorker]] = []

    title: str = ""

    async def do_simulation(self):
        """
        Instantiate simulation entities, emit initial event, and run coroutines
        that will emit subsequent events.
        """
        server, apps, wworkers, aworkers = (
            Server(),
            [cls() for cls in self.application_classes],
            [WorkflowWorker(self.workflow_classes)],
            [cls() for cls in self.activity_worker_classes],
        )
        emit_init_event(
            server, apps, wworkers, aworkers, self.title or self.__class__.__name__
        )

        coros: list[Coroutine] = [w.poll(server) for w in wworkers + aworkers]
        for app in apps:
            coros.extend(app.get_coroutines(server))

        await run_coroutines(coros)


async def run_coroutines(coros: list[Coroutine]):
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(coro) for coro in coros]
            # TODO: race?
            Entity.terminate_simulation = lambda _: [t.cancel() for t in tasks]

    except ExceptionGroup as eg:
        print(f"Caught ExceptionGroup:", file=sys.stderr)
        for e in eg.exceptions:
            print(f"    {e}", file=sys.stderr)
            traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        sys.exit(1)


def run_simulation(simulation: Simulation):
    asyncio.run(simulation.do_simulation())
