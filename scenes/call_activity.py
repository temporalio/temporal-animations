from scenes.execute_workflow import ExecuteWorkflowApplication
from tempyral.scene import TemporalScene
from tempyral.simulation import Workflow


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


class CallActivity(TemporalScene):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [CallActivityWorkflow]
