from scenes.scene import TemporalScene, run_simulation
from tempyral import Application, Workflow


class ExecuteWorkflowApplication(Application):
    """
    An application that executes a workflow
    """

    go = """
workflowRun, err := c.ExecuteWorkflow(          // tempyral: ApplicationRequestType.ExecuteWorkflow "my-workflow-id"
    ctx, workflowOptions, workflows.MyWorkflow)
if err != nil {
    log.Fatalln("Unable to execute workflow", err)
}
var result string
err = workflowRun.Get(ctx, &result)
"""


class NoOpWorkflow(Workflow):
    """
    A workflow that does nothing.
    """

    go = """
func MyWorkflow(ctx workflow.Context) error {
    return nil                                  // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION
}
"""


class ExecuteWorkflow(TemporalScene):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(ExecuteWorkflow())
