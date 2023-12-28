from typing import Coroutine, Iterable

from tempyral.scene import TemporalScene
from tempyral.simulation import Application, Server, Workflow


class CallActivityWorkflow(Workflow):
    """
    A workflow that calls an activity.
    """

    go = """
func MyWorkflow(ctx workflow.Context) (int, error) {
    var result int
    workflow.ExecuteActivity(MyActivity).Get(ctx, &result) // tempyral: CommandType.SCHEDULE_ACTIVITY_TASK
    return result, nil
}
"""
    workflow_id = "call-activity-workflow"


class CallActivity(TemporalScene):
    workflow_classes = [CallActivityWorkflow]

    def simulation(
        self,
        app: Application,
        server: Server,
    ) -> Iterable[Coroutine]:
        yield app.start_workflow(CallActivityWorkflow.workflow_id, server)
