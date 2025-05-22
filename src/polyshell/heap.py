"""A simple PriorityQueue implementation with fast removal."""

from heapq import heappop, heappush
from itertools import count


class PriorityQueue:
    REMOVED = "REMOVED"

    def __init__(self):
        """Initialize the priority queue."""
        self.pq = []
        self.entry_map = {}
        self.counter = count()

    def push(self, index: int, priority: float) -> None:
        """Push an item to the queue, overwriting previous entries."""
        if index in self.entry_map:
            self.remove(index)
        entry = [priority, next(self.counter), index]
        self.entry_map[index] = entry
        heappush(self.pq, entry)

    def pop(self) -> tuple[int, float]:
        """Pop an item from the queue with lowest priority."""
        while self.pq:
            priority, _, index = heappop(self.pq)
            if index is not self.REMOVED:
                del self.entry_map[index]
                return index, priority
        else:
            raise ValueError("pop from any empty priority queue.")

    def remove(self, index: int) -> None:
        """Mark an entry as removed."""
        entry = self.entry_map.pop(index)
        entry[-1] = self.REMOVED

    def __contains__(self, index: int) -> bool:
        return index in self.entry_map
