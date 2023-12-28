from typing import Coroutine, Iterable

from tempyral.scene import TemporalScene
from tempyral.simulation import Application, Server, Workflow


class NoOpWorkflow(Workflow):
    """
    A workflow that does nothing.
    """

    go = """
func MyWorkflow(ctx workflow.Context) error {
    return nil
}
"""
    workflow_id = "noop-workflow"


class ExecuteWorkflow(TemporalScene):
    workflow_classes = [NoOpWorkflow]

    def simulation(
        self,
        app: Application,
        server: Server,
    ) -> Iterable[Coroutine]:
        yield app.start_workflow(NoOpWorkflow.workflow_id, server)
