from asyncio import Queue
from typing import TYPE_CHECKING, cast

from schema import models

if TYPE_CHECKING:
    import tempyral


def make_state_change_event(
    entity: "tempyral.Entity",
) -> models.StateChangeEvent:
    return models.StateChangeEvent(entity=entity.as_serializable())


def make_message_event(
    sender: "tempyral.Entity",
    receiver: "tempyral.Entity",
    message: "tempyral.RequestResponse | tempyral.Response",
) -> models.MessageEvent:
    return models.MessageEvent(
        sender=sender.as_serializable(),
        receiver=receiver.as_serializable(),
        message=cast(models.RequestResponse, message.as_serializable()),
    )


class EventBus:
    def __init__(self):
        self.bus: Queue[models.StateChangeEvent | models.MessageEvent] = Queue()

    async def publish(self, event: models.StateChangeEvent | models.MessageEvent):
        await self.bus.put(event)

    def empty(self) -> bool:
        return self.bus.empty()


event_bus = EventBus()
