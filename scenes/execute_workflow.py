from tempyral.scene import TemporalScene
from tempyral.simulation import Application, Workflow


class ExecuteWorkflowApplication(Application):
    """
    An application that executes a workflow
    """

    go = """
c, err := client.Dial(client.Options{})
workflowOptions := client.StartWorkflowOptions{
    ID:        "my-workflow-id",
    TaskQueue: "my-task-queue",
}
workflowRun, err := c.ExecuteWorkflow(ctx, workflowOptions, workflows.MyWorkflow) // tempyral: ApplicationRequestType.StartWorkflowExecution "my-workflow-id"
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
