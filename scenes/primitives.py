from tempyral.scene import TemporalScene
from tempyral.simulation import (
    ActivityWorker,
    Application,
    CallActivityWorkflowWorker,
    NoOpWorkflowWorker,
    Server,
)


class ExecuteWorkflow(TemporalScene):
    workflow_worker_cls = NoOpWorkflowWorker

    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: workflow_worker_cls,
        _: ActivityWorker,
    ):
        yield app.start_workflow(workflow_worker.workflow.workflow_id, server)
        yield workflow_worker.poll(server)


class CallActivity(TemporalScene):
    workflow_worker_cls = CallActivityWorkflowWorker

    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: workflow_worker_cls,
        activity_worker: ActivityWorker,
    ):
        yield app.start_workflow(workflow_worker.workflow.workflow_id, server)
        yield workflow_worker.poll(server)
        yield activity_worker.poll(server)
