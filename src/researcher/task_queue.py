from __future__ import annotations

from dataclasses import dataclass
from queue import PriorityQueue
from typing import Any

@dataclass(order=True)
class QueueItem:
    priority: int
    sequence: int
    task_id: str
    payload: Any = None

class TaskQueue:
    """In-memory priority queue for the MVP.

    A durable queue will replace this component without changing task models.
    """

    def __init__(self) -> None:
        self._queue: PriorityQueue[QueueItem] = PriorityQueue()
        self._sequence = 0

    def push(self, task_id: str, payload: Any = None, priority: int = 100) -> None:
        self._sequence += 1
        self._queue.put(QueueItem(priority, self._sequence, task_id, payload))

    def pop(self) -> QueueItem:
        return self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()
