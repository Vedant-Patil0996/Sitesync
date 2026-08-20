from typing import Dict, List
import asyncio
import json
from datetime import datetime


class EventManager:
    """
    Manages WebSocket connections per run_id.
    Acts as an in-process event bus using asyncio queues.
    Each run gets its own list of subscriber queues (one per WS connection).
    """

    def __init__(self):
        # run_id -> list of asyncio.Queue
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Create a new subscriber queue for a run and return it."""
        q: asyncio.Queue = asyncio.Queue()
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue):
        """Remove a subscriber queue when the WebSocket disconnects."""
        if run_id in self._subscribers:
            try:
                self._subscribers[run_id].remove(q)
            except ValueError:
                pass
            if not self._subscribers[run_id]:
                del self._subscribers[run_id]

    async def publish(self, run_id: str, event: dict):
        """Push an event to all subscribers of a run."""
        if run_id not in self._subscribers:
            return
        dead = []
        for q in self._subscribers[run_id]:
            try:
                await q.put(event)
            except Exception:
                dead.append(q)
        for q in dead:
            self.unsubscribe(run_id, q)

    def publish_sync(self, run_id: str, event: dict, loop: asyncio.AbstractEventLoop):
        """
        Thread-safe publish from a synchronous context (e.g., subprocess thread).
        Schedules the coroutine on the given event loop.
        """
        asyncio.run_coroutine_threadsafe(self.publish(run_id, event), loop)

    def has_subscribers(self, run_id: str) -> bool:
        return run_id in self._subscribers and len(self._subscribers[run_id]) > 0


# Singleton instance — imported everywhere
event_manager = EventManager()
