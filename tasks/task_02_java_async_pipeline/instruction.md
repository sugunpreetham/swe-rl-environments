# Task 02: Asynchronous Resilient Order Pipeline with Compensation

## Domain
Enterprise Java 17+, Distributed Transactions, Non-Blocking Asynchronous DAGs

## Context & Problem Description
You are maintaining the core order processing pipeline for an e-commerce microservices platform. The current service executes transactions sequentially and synchronously:
1. `validate(order)`
2. `reserveInventory(order)`
3. `processPayment(order)`
4. `notifyFulfillment(order)`

Under flash-sale peak load, this architecture experiences critical production outages:
* **Thread Pool Starvation:** Synchronous blocking waits on downstream HTTP/RPC dependencies hold thread resources, exhausting application server worker pools.
* **Inconsistent Distributed State (Lack of Saga Compensation):** If payment processing fails or times out *after* inventory has been successfully reserved, the system fails to release the reserved inventory, stranding stock in an unrecoverable state.
* **No Cascading Timeout Guard:** Downstream payment gateway stalls hang indefinitely without bounded timeouts.

## Requirements
Refactor `OrderPipeline.java` to fulfill the following architectural requirements:
1. **Asynchronous Non-Blocking Execution:**
   - Execute stages using Java's `CompletableFuture` pipeline without blocking threads.
2. **Deterministic Transactional Rollback (Saga Compensation):**
   - If payment fails, times out, or throws an exception, the pipeline MUST immediately and asynchronously trigger `inventoryService.releaseInventory(order.getId())` to rollback the reservation before completing the future exceptionally.
3. **Explicit Timeout Bounds:**
   - Enforce an asynchronous timeout boundary of 1,500ms on the payment stage using `.orTimeout()`.
4. **Idempotency & Concurrent Safety:**
   - Ensure the pipeline can safely handle concurrent requests without double-allocating inventory or leaking unhandled completion exceptions.

## Verification
The verifier runs deterministic JUnit 5 test suites covering:
* Asynchronous thread decoupling (assertions verifying non-blocking execution)
* Fault-injection rollback (verifying inventory release upon payment rejection)
* Timeout resilience (verifying pipeline failure within 1.5s when payment hangs)
* Dynamic randomized order IDs to prevent hardcoded outputs.
