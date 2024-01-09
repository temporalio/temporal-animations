from scenes.ExecuteWorkflow import ExecuteWorkflowApplication
from tempyral.simulation import Simulation, run_simulation
from tempyral.worker import ActivityWorker, Workflow


class CallActivityWorkflow(Workflow):
    """
    A workflow that calls an activity.
    """

    go = """
func MyWorkflow(ctx workflow.Context) (int, error) {
    var result int
    workflow.ExecuteActivity(MyActivity).Get(ctx, &result) // tempyral: CommandType.SCHEDULE_ACTIVITY_TASK
    return result, nil                                     // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION 0
}
"""


class CallActivity(Simulation):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [CallActivityWorkflow]
    activity_worker_classes = [ActivityWorker]


if __name__ == "__main__":
    run_simulation(CallActivity())
