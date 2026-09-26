# Task 01: High-Throughput Concurrent LRU + TTL Cache

## Domain
Backend Concurrency, Memory Management & Race Condition Resolution (Python 3.11+)

## Context & Problem Description
You are maintaining a high-performance in-memory caching module `ConcurrentLRUTTLCache` used in a microservice API gateway handling 10,000+ requests per second.

The existing implementation in `workspace/cache.py` suffers from three critical production bugs:
1. **Concurrency Race Condition:** Under high-concurrency read/write operations across multiple worker threads, node operations on the doubly-linked list (`_remove_node`, `_add_node_to_head`) experience interleaving races. This leads to `KeyError`, disconnected pointers, or silent data corruption.
2. **Clock Drift Susceptibility:** Expiration checks rely on `time.time()`, which is vulnerable to system wall-clock adjustments (e.g., NTP synchronization jumps) causing premature eviction of active items.
3. **Cyclic Reference Memory Leak:** Evicted/deleted nodes retain bidirectional references (`prev` and `next`), preventing Python's reference counter from immediately freeing memory until the cyclic garbage collector runs.
4. **Performance Bottleneck:** The cache currently uses a coarse-grained global lock that serializes all reads, dropping throughput under heavy read concurrency.

## Requirements
Modify `cache.py` so that:
- All operations (`get`, `put`, `delete`, `cleanup_expired`, `size`) are strictly thread-safe.
- Uses `time.monotonic()` for deterministic TTL tracking.
- Nodes removed from the cache must have their `prev` and `next` pointers severed to guarantee immediate garbage collection.
- Thread-safe eviction strictly preserves the $O(1)$ LRU order and removes expired items lazily on access or proactively during capacity limits.
- Supports generic keys and values with optional TTL (in seconds).
- Passes all deterministic verification tiers: functional correctness, concurrent stress fuzzing, dynamic anti-cheat key validation, and memory leak verifications.

## Anti-Cheating & Integrity Notice
Do not hardcode test keys, mock timestamps, or bypass eviction constraints. The verifier uses cryptographically seeded random payloads and inspects heap references.
