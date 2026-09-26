import threading
import time
from typing import Any, Optional, Dict

class Node:
    __slots__ = ("key", "val", "expire_at", "prev", "next")

    def __init__(self, key: Any, val: Any, expire_at: Optional[float] = None):
        self.key = key
        self.val = val
        self.expire_at = expire_at
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None

class ConcurrentLRUTTLCache:
    """
    GOLDEN REFERENCE IMPLEMENTATION:
    - Reentrant Lock (RLock) guaranteeing thread-safety across atomic operations.
    - Deterministic time.monotonic() to eliminate wall-clock / NTP drift.
    - Explicit pointer severance on deleted/evicted nodes to prevent cyclic memory leaks.
    - Atomic lazy-expiration on read and bounded LRU eviction under capacity limits.
    """
    def __init__(self, capacity: int, default_ttl_sec: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("Capacity must be strictly positive")
        self.capacity = int(capacity)
        self.default_ttl = float(default_ttl_sec) if default_ttl_sec is not None else None
        self._map: Dict[Any, Node] = {}
        self._lock = threading.RLock()
        
        # Sentinel dummy nodes
        self._head = Node(None, None)
        self._tail = Node(None, None)
        self._head.next = self._tail
        self._tail.prev = self._head

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    def _is_expired(self, node: Node, current_time: float) -> bool:
        if node.expire_at is None:
            return False
        return current_time >= node.expire_at

    def _remove_node(self, node: Node) -> None:
        p = node.prev
        n = node.next
        if p:
            p.next = n
        if n:
            n.prev = p
        # Sever links to guarantee prompt GC reclamation
        node.prev = None
        node.next = None

    def _add_to_head(self, node: Node) -> None:
        node.next = self._head.next
        node.prev = self._head
        if self._head.next:
            self._head.next.prev = node
        self._head.next = node

    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            if key not in self._map:
                return None
            node = self._map[key]
            now = self._now()
            if self._is_expired(node, now):
                # Lazy eviction
                self._remove_node(node)
                del self._map[key]
                return None
            
            # Move to head (most recently used)
            self._remove_node(node)
            self._add_to_head(node)
            return node.val

    def put(self, key: Any, val: Any, ttl_sec: Optional[float] = None) -> None:
        with self._lock:
            now = self._now()
            ttl = ttl_sec if ttl_sec is not None else self.default_ttl
            expire_at = (now + ttl) if ttl is not None else None

            if key in self._map:
                node = self._map[key]
                node.val = val
                node.expire_at = expire_at
                self._remove_node(node)
                self._add_to_head(node)
                return

            # Check if capacity reached
            if len(self._map) >= self.capacity:
                # First, purge any already expired nodes from tail
                purged = False
                curr = self._tail.prev
                while curr and curr != self._head:
                    prev_node = curr.prev
                    if self._is_expired(curr, now):
                        self._remove_node(curr)
                        if curr.key in self._map:
                            del self._map[curr.key]
                        purged = True
                        break
                    curr = prev_node

                # If no expired node was purged, evict strict LRU (tail.prev)
                if not purged:
                    lru = self._tail.prev
                    if lru and lru != self._head:
                        self._remove_node(lru)
                        if lru.key in self._map:
                            del self._map[lru.key]

            new_node = Node(key, val, expire_at)
            self._add_to_head(new_node)
            self._map[key] = new_node

    def delete(self, key: Any) -> bool:
        with self._lock:
            if key in self._map:
                node = self._map.pop(key)
                self._remove_node(node)
                return True
            return False

    def cleanup_expired(self) -> int:
        """Proactively purges all expired entries; returns count of removed items."""
        with self._lock:
            now = self._now()
            expired_keys = [k for k, node in self._map.items() if self._is_expired(node, now)]
            for k in expired_keys:
                node = self._map.pop(k, None)
                if node:
                    self._remove_node(node)
            return len(expired_keys)

    def size(self) -> int:
        with self._lock:
            return len(self._map)

    def clear(self) -> None:
        with self._lock:
            curr = self._head.next
            while curr and curr != self._tail:
                nxt = curr.next
                curr.prev = None
                curr.next = None
                curr = nxt
            self._map.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
