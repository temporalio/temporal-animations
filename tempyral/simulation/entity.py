import asyncio

from tempyral.event_bus import MessageEvent, StateChangeEvent, event_bus


class Entity:
    async def publish_change_event(self, **kwargs):
        await event_bus.publish(StateChangeEvent(self, kwargs))
        await asyncio.sleep(0)

    async def publish_message_event(
        self, sender: "Entity", receiver: "Entity", **kwargs
    ):
        if event_bus is not None:
            await event_bus.publish(MessageEvent(sender, receiver, kwargs))
            await asyncio.sleep(0)
