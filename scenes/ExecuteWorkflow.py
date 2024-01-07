from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation
from tempyral.worker import Workflow


class ExecuteWorkflowApplication(Application):
    """
    An application that executes a workflow
    """

    go = """
workflowRun, err := c.ExecuteWorkflow(          // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    ctx, workflowOptions, workflows.MyWorkflow)
if err != nil {
    log.Fatalln("Unable to execute workflow", err)
}
var result string
err = workflowRun.Get(ctx, &result)            // tempyral: ApplicationRequestType.GetWorkflowResult "my-workflow-id"
"""


class NoOpWorkflow(Workflow):
    """
    A workflow that does nothing.
    """

    go = """
func MyWorkflow(ctx workflow.Context) error {
    return 1                                  // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION 1
}
"""


class ExecuteWorkflow(Simulation):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(ExecuteWorkflow())
