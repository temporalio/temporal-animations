from tempyral.scene import TemporalScene
from tempyral.simulation import Application, Workflow


class ExecuteWorkflowApplication(Application):
    """
    An application that executes a workflow
    """

    go = """
workflowRun, err := c.ExecuteWorkflow(          // tempyral: ApplicationRequestType.StartWorkflowExecution "my-workflow-id"
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
    return nil
}
"""


class ExecuteWorkflow(TemporalScene):
    application_classes = [ExecuteWorkflowApplication]
    workflow_classes = [NoOpWorkflow]
