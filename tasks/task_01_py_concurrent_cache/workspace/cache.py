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
    BUGGY INITIAL IMPLEMENTATION:
    - Missing lock on critical pointer mutations causing races in multi-threaded environments.
    - Uses wall-clock time.time() vulnerable to NTP adjustments.
    - Leaves circular references on deleted/evicted nodes causing memory leaks.
    """
    def __init__(self, capacity: int, default_ttl_sec: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.default_ttl = default_ttl_sec
        self.map: Dict[Any, Node] = {}
        
        # Dummy head and tail
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _now(self) -> float:
        # BUG: uses wall-clock instead of monotonic clock
        return time.time()

    def _is_expired(self, node: Node) -> bool:
        if node.expire_at is None:
            return False
        return self._now() > node.expire_at

    def _remove_node(self, node: Node):
        # BUG: Unsafe without synchronizing pointer updates under concurrency
        p = node.prev
        n = node.next
        if p:
            p.next = n
        if n:
            n.prev = p
        # BUG: Fails to sever node.prev and node.next, creating lingering reference cycles

    def _add_to_head(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: Any) -> Optional[Any]:
        # BUG: Race condition between lookup and eviction check
        if key not in self.map:
            return None
        node = self.map[key]
        if self._is_expired(node):
            self.delete(key)
            return None
        
        self._remove_node(node)
        self._add_to_head(node)
        return node.val

    def put(self, key: Any, val: Any, ttl_sec: Optional[float] = None) -> None:
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl
        expire_at = (self._now() + ttl) if ttl is not None else None

        if key in self.map:
            node = self.map[key]
            node.val = val
            node.expire_at = expire_at
            self._remove_node(node)
            self._add_to_head(node)
            return

        if len(self.map) >= self.capacity:
            # Evict LRU (node before tail)
            lru = self.tail.prev
            if lru and lru != self.head:
                self._remove_node(lru)
                if lru.key in self.map:
                    del self.map[lru.key]

        new_node = Node(key, val, expire_at)
        self._add_to_head(new_node)
        self.map[key] = new_node

    def delete(self, key: Any) -> bool:
        if key in self.map:
            node = self.map.pop(key)
            self._remove_node(node)
            return True
        return False

    def size(self) -> int:
        return len(self.map)
