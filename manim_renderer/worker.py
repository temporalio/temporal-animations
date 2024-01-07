from manim import DOWN, LEFT, SMALL_BUFF, Mobject, VDict

from manim_renderer import style
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import ProxyEntity, ProxyEntityWithChildren
from schema import schema


class ActivityTaskRequest(ProxyEntity[schema.WorkerPollRequest]):
    def render(self, entity: schema.WorkerPollRequest) -> Mobject:
        if entity.stage == schema.RequestResponseStage.Request:
            return style.invisible_message()
        else:
            return style.message("Activity Task")


class ActivityTaskCompleted(ProxyEntity[schema.ActivityTaskCompleted]):
    def render(self, _: schema.ActivityTaskCompleted) -> Mobject:
        return style.message("Activity Task Completed")


class ActivityWorker(ProxyEntityWithCode[schema.ActivityWorker]):
    def render(self, entity: schema.ActivityWorker) -> Mobject:
        code = super().render(entity)
        text = self.with_time(style.actor("Activity Worker"), entity)
        return VDict({"text": text, "code": code}).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )


class WorkflowTaskCompleted(ProxyEntity[schema.WorkflowTaskCompleted]):
    def render(self, _: schema.WorkflowTaskCompleted) -> Mobject:
        return style.message("WFT Completed")


class WorkerRequest(ProxyEntity[schema.WorkerRequest]):
    def render(self, entity: schema.WorkerRequest) -> Mobject:
        return style.message(f"WorkerRequest[{entity.__class__.__name__}]")


class Workflow(ProxyEntityWithCode[schema.Workflow]):
    pass


class WorkflowWorker(
    ProxyEntityWithChildren[schema.WorkflowWorker, schema.Workflow, Workflow]
):
    child_cls = Workflow
    child_align_direction = LEFT

    def render(self, entity: schema.WorkflowWorker) -> Mobject:
        return self.with_time(style.actor("Workflow Worker"), entity)

    def render_to_scene(self, entity: schema.WorkflowWorker):
        super().render_to_scene(entity)
        self.scene.wait()

    @staticmethod
    def get_child_entities(
        entity: schema.WorkflowWorker,
    ) -> list[schema.Workflow]:
        return entity.workflows
