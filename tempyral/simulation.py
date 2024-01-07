import asyncio
import sys
import traceback
from typing import Coroutine, Type

from common.utils import debug
from tempyral.application import Application
from tempyral.entity import Entity
from tempyral.event import emit_init_event
from tempyral.server import Server
from tempyral.worker import ActivityWorker, Workflow, WorkflowWorker


class Simulation:
    application_classes: list[Type[Application]]
    workflow_classes: list[Type[Workflow]]

    async def do_simulation(self):
        """
        Instantiate simulation entities, emit initial event, and run coroutines
        that will emit subsequent events.
        """
        server, apps, wworkers, aworkers = (
            Server(),
            [cls() for cls in self.application_classes],
            [WorkflowWorker(self.workflow_classes)],
            [ActivityWorker()],
        )
        emit_init_event(server, apps, wworkers, aworkers)

        coros: list[Coroutine] = [w.poll(server) for w in wworkers + aworkers]
        for app in apps:
            coros.extend(app.get_coroutines(server))

        await _run_coros(coros)


async def _run_coros(coros: list[Coroutine]):
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(debug(coro)) for coro in coros]
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
