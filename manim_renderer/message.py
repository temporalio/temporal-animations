from typing import Generic, Protocol

from manim_renderer.entity import E, MessageStage, ProxyEntity, VisualElement


class HasMessageStage(Protocol):
    message_stage: MessageStage


class Message(VisualElement, HasMessageStage):
    pass


class ProxyEntityMessage(ProxyEntity, HasMessageStage, Generic[E]):
    pass
