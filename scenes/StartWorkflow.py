from manim_renderer.scene import TemporalScene, run_simulation
from scenes.ExecuteWorkflow import NoOpWorkflow
from tempyral import Application


class StartWorkflowApplication(Application):
    """
    An application that starts a workflow.
    """

    typescript = """
const wfHandle = await handle.client.start(myWorkflow, {        // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
"""


class StartWorkflow(TemporalScene):
    application_classes = [StartWorkflowApplication]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(StartWorkflow())
