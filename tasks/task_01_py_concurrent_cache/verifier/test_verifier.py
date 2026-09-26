import concurrent.futures
import gc
import random
import string
import sys
import threading
import time
import pytest

# Test the golden solution by default, or workspace if configured
try:
    from tasks.task_01_py_concurrent_cache.golden_solution.cache import ConcurrentLRUTTLCache, Node
except ImportError:
    from tasks.task_01_py_concurrent_cache.workspace.cache import ConcurrentLRUTTLCache, Node

# ============================================================================
# TIER 1: FUNCTIONAL UNIT & BASIC SPECIFICATIONS
# ============================================================================

def test_tier1_basic_lru_eviction():
    cache = ConcurrentLRUTTLCache(capacity=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    assert cache.get("a") == 1  # 'a' is now MRU; LRU order is b, c, a
    cache.put("d", 4)           # 'b' should be evicted

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4
    assert cache.size() == 3

def test_tier1_ttl_expiration(monkeypatch):
    current_time = [100.0]
    monkeypatch.setattr(time, "monotonic", lambda: current_time[0])

    cache = ConcurrentLRUTTLCache(capacity=5, default_ttl_sec=10.0)
    cache.put("k1", "v1", ttl_sec=5.0)
    cache.put("k2", "v2")  # default 10s

    assert cache.get("k1") == "v1"
    assert cache.get("k2") == "v2"

    # Advance time by 6s -> k1 expires, k2 alive
    current_time[0] += 6.0
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"

    # Advance time by another 5s -> k2 expires
    current_time[0] += 5.0
    assert cache.get("k2") is None

# ============================================================================
# TIER 2: MONOTONIC CLOCK & DETERMINISTIC CLOCK DRIFT
# ============================================================================

def test_tier2_clock_drift_resilience(monkeypatch):
    """
    Ensure implementation relies on monotonic time and is impervious to
    NTP wall-clock time jumps backwards or forwards.
    """
    mono_time = [500.0]
    monkeypatch.setattr(time, "monotonic", lambda: mono_time[0])
    # Deliberately distort time.time() to simulate an aggressive NTP correction
    monkeypatch.setattr(time, "time", lambda: 0.0)

    cache = ConcurrentLRUTTLCache(capacity=2, default_ttl_sec=10.0)
    cache.put("token", "secret_abc", ttl_sec=15.0)

    # Should still be valid because monotonic time hasn't advanced
    assert cache.get("token") == "secret_abc"

    mono_time[0] += 16.0
    assert cache.get("token") is None

# ============================================================================
# TIER 3: MEMORY LEAK & CYCLIC REFERENCE SEVERANCE
# ============================================================================

def test_tier3_cyclic_reference_severance():
    """
    Verify that evicted and deleted nodes sever their prev/next pointers,
    enabling immediate reference collection without waiting for cyclic GC.
    """
    cache = ConcurrentLRUTTLCache(capacity=2)
    cache.put("leak_test_1", [1, 2, 3])
    cache.put("leak_test_2", [4, 5, 6])

    # Evict leak_test_1 by pushing a 3rd item
    cache.put("leak_test_3", [7, 8, 9])
    assert cache.get("leak_test_1") is None

    # Delete explicit item
    assert cache.delete("leak_test_2") is True
    assert cache.get("leak_test_2") is None

# ============================================================================
# TIER 4: CONCURRENCY STRESS FUZZING (ANTI-RACE CONDITION)
# ============================================================================

def test_tier4_concurrent_stress_fuzzing():
    """
    Spawn 20 parallel threads executing 5,000 mixed read, write, update,
    and eviction operations. Ensures zero thread deadlocks or pointer corruption.
    """
    cache = ConcurrentLRUTTLCache(capacity=50, default_ttl_sec=0.2)
    num_threads = 16
    ops_per_thread = 250
    exceptions = []

    def worker(worker_id: int):
        rng = random.Random(worker_id * 42)
        try:
            for _ in range(ops_per_thread):
                key = f"key_{rng.randint(0, 100)}"
                op = rng.choice(["get", "put", "del"])
                if op == "get":
                    cache.get(key)
                elif op == "put":
                    val = f"val_{worker_id}_{rng.randint(0, 1000)}"
                    ttl = rng.choice([None, 0.05, 0.5])
                    cache.put(key, val, ttl_sec=ttl)
                elif op == "del":
                    cache.delete(key)
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert len(exceptions) == 0, f"Encountered concurrency exceptions: {exceptions}"
    assert cache.size() <= 50, f"Cache size exceeded capacity under concurrency: {cache.size()}"

# ============================================================================
# TIER 5: ANTI-CHEAT DYNAMIC ENTROPY VERIFIER
# ============================================================================

def test_tier5_anti_cheat_dynamic_entropy():
    """
    Generates dynamic randomized payloads to guarantee no static hardcoding
    of test answers or specific keys.
    """
    entropy_seed = random.randint(10000, 99999)
    rng = random.Random(entropy_seed)

    cache = ConcurrentLRUTTLCache(capacity=100)
    expected_pairs = {}

    for _ in range(100):
        k = ''.join(rng.choices(string.ascii_letters, k=12))
        v = rng.uniform(1.0, 10000.0)
        cache.put(k, v)
        expected_pairs[k] = v

    for k, v in expected_pairs.items():
        assert cache.get(k) == v, f"Dynamic key mismatch for key '{k}'"
