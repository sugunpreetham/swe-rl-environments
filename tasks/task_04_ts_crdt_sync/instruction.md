# Task 04: Observed-Remove Set (OR-Set) CRDT State Convergence

## Domain
Distributed Systems, Conflict-Free Replicated Data Types (CRDTs), TypeScript 5.0+

## Context & Problem Description
You are engineering a peer-to-peer distributed data replication engine for an offline-first collaborative workspace. Nodes maintain local state and synchronize asynchronously over unpredictable, high-latency network meshes.

The data synchronization engine relies on an **Observed-Remove Set (OR-Set)** with Vector Clocks. However, under network partition and out-of-order packet delivery, the current implementation fails:
1. **Add-Wins Inconsistency:** When Peer A concurrently removes an element while Peer B re-adds it, the set drops the element on Peer A but retains it on Peer B, violating Strong Eventual Consistency (SEC).
2. **Premature Tombstone Pruning:** Elements removed during a temporary partition are resurrected if a delayed packet from an older state arrives later.
3. **Non-Deterministic State Divergence:** Commutativity is broken when merging states arriving in reverse chronological order.

## Requirements
Refactor `src/crdt.ts` to implement a mathematically sound, deterministic Add-Wins OR-Set CRDT:
- **Unique Tag Generation:** Each `add(element)` operation must generate a globally unique tag (e.g., combining `peerId` and local monotonic counter).
- **Add-Wins Semantics:** An element exists in the set if and only if there is at least one active tag that has not been explicitly removed.
- **Commutative & Associative Merge:** Merging state between any two peers $A$ and $B$ must produce identical results regardless of order:
  $$\text{merge}(A, B) = \text{merge}(B, A)$$
  $$\text{merge}(\text{merge}(A, B), C) = \text{merge}(A, \text{merge}(B, C))$$
- **Tombstone Monotonicity:** Ensure that deleted tags are permanently suppressed against delayed re-adds with older vector clock timestamps.

## Verification
The test suite executes:
- Basic add, remove, and query unit specifications.
- Network partition simulation: peers diverge locally, then merge out-of-order and assert identical state.
- Add-Wins race condition verification.
- Dynamic randomized payload fuzzing across simulated multi-peer meshes.
