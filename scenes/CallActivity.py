from scenes.ExecuteWorkflow import ExecuteWorkflowApplication
from scenes.scene import TemporalScene, run_simulation
from tempyral import Workflow


class CallActivityWorkflow(Workflow):
    """
    A workflow that calls an activity.
    """

    go = """
func MyWorkflow(ctx workflow.Context) (int, error) {
    var result int
    workflow.ExecuteActivity(MyActivity).Get(ctx, &result) // tempyral: CommandType.SCHEDULE_ACTIVITY_TASK
    return result, nil                                     // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION
}
"""


class CallActivity(TemporalScene):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [CallActivityWorkflow]


if __name__ == "__main__":
    run_simulation(CallActivity())
