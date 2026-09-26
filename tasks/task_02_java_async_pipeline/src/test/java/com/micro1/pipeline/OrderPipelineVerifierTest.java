package com.micro1.pipeline;

import com.micro1.pipeline.model.Order;
import com.micro1.pipeline.service.InventoryService;
import com.micro1.pipeline.service.PaymentService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.junit.jupiter.api.Assertions.*;

public class OrderPipelineVerifierTest {

    @Test
    @DisplayName("Tier 1: Successful Asynchronous Pipeline Execution")
    void testSuccessfulOrderPipeline() throws Exception {
        AtomicBoolean inventoryReserved = new AtomicBoolean(false);
        AtomicBoolean paymentCharged = new AtomicBoolean(false);

        InventoryService mockInventory = new InventoryService() {
            @Override
            public CompletableFuture<Boolean> reserveInventory(String orderId, String itemId, int quantity) {
                inventoryReserved.set(true);
                return CompletableFuture.completedFuture(true);
            }
            @Override
            public CompletableFuture<Void> releaseInventory(String orderId) {
                return CompletableFuture.completedFuture(null);
            }
        };

        PaymentService mockPayment = (orderId, amount) -> {
            paymentCharged.set(true);
            return CompletableFuture.completedFuture("TXN_12345");
        };

        OrderPipeline pipeline = new OrderPipeline(mockInventory, mockPayment);
        Order order = new Order("ORD-001", "CUST-A", "ITEM-X", 2, new BigDecimal("49.99"));

        CompletableFuture<String> future = pipeline.processOrderAsync(order);
        String txnId = future.get(3, TimeUnit.SECONDS);

        assertEquals("TXN_12345", txnId);
        assertTrue(inventoryReserved.get(), "Inventory must be reserved");
        assertTrue(paymentCharged.get(), "Payment must be charged");
    }

    @Test
    @DisplayName("Tier 2: Transactional Rollback (Compensation) on Payment Failure")
    void testCompensationRollbackOnPaymentFailure() {
        AtomicBoolean inventoryReleased = new AtomicBoolean(false);

        InventoryService mockInventory = new InventoryService() {
            @Override
            public CompletableFuture<Boolean> reserveInventory(String orderId, String itemId, int quantity) {
                return CompletableFuture.completedFuture(true);
            }
            @Override
            public CompletableFuture<Void> releaseInventory(String orderId) {
                inventoryReleased.set(true);
                return CompletableFuture.completedFuture(null);
            }
        };

        PaymentService mockPayment = (orderId, amount) ->
            CompletableFuture.failedFuture(new RuntimeException("Card declined"));

        OrderPipeline pipeline = new OrderPipeline(mockInventory, mockPayment);
        Order order = new Order("ORD-FAIL-01", "CUST-B", "ITEM-Y", 1, new BigDecimal("100.00"));

        ExecutionException ex = assertThrows(ExecutionException.class, () ->
            pipeline.processOrderAsync(order).get(3, TimeUnit.SECONDS)
        );

        assertTrue(ex.getMessage().contains("Card declined"));
        assertTrue(inventoryReleased.get(), "Saga compensation must release reserved inventory when payment fails!");
    }

    @Test
    @DisplayName("Tier 3: Payment Timeout Enforces Asynchronous Rollback")
    void testPaymentTimeoutCompensation() {
        AtomicBoolean inventoryReleased = new AtomicBoolean(false);

        InventoryService mockInventory = new InventoryService() {
            @Override
            public CompletableFuture<Boolean> reserveInventory(String orderId, String itemId, int quantity) {
                return CompletableFuture.completedFuture(true);
            }
            @Override
            public CompletableFuture<Void> releaseInventory(String orderId) {
                inventoryReleased.set(true);
                return CompletableFuture.completedFuture(null);
            }
        };

        // Payment that hangs for 5 seconds
        PaymentService mockHangingPayment = (orderId, amount) ->
            CompletableFuture.supplyAsync(() -> {
                try {
                    Thread.sleep(5000);
                } catch (InterruptedException ignored) {}
                return "TXN_LATE";
            });

        // Set short 500ms timeout for test
        OrderPipeline pipeline = new OrderPipeline(mockInventory, mockHangingPayment, ForkJoinPool.commonPool(), 500);
        Order order = new Order("ORD-TIMEOUT-01", "CUST-C", "ITEM-Z", 1, new BigDecimal("25.00"));

        long start = System.currentTimeMillis();
        ExecutionException ex = assertThrows(ExecutionException.class, () ->
            pipeline.processOrderAsync(order).get(3, TimeUnit.SECONDS)
        );
        long elapsed = System.currentTimeMillis() - start;

        assertTrue(elapsed < 2000, "Pipeline should fail promptly via timeout");
        assertTrue(inventoryReleased.get(), "Inventory must be rolled back on payment gateway timeout!");
    }

    @Test
    @DisplayName("Tier 4: Anti-Cheat Dynamic Entropy Verification")
    void testAntiCheatDynamicEntropy() throws Exception {
        String randomOrderId = "ORD-" + UUID.randomUUID();
        BigDecimal randomAmount = new BigDecimal(ThreadLocalRandom.current().nextInt(10, 500) + ".75");

        InventoryService mockInventory = new InventoryService() {
            @Override
            public CompletableFuture<Boolean> reserveInventory(String orderId, String itemId, int quantity) {
                assertEquals(randomOrderId, orderId);
                return CompletableFuture.completedFuture(true);
            }
            @Override
            public CompletableFuture<Void> releaseInventory(String orderId) {
                return CompletableFuture.completedFuture(null);
            }
        };

        PaymentService mockPayment = (orderId, amount) -> {
            assertEquals(randomOrderId, orderId);
            assertEquals(randomAmount, amount);
            return CompletableFuture.completedFuture("TXN_" + orderId);
        };

        OrderPipeline pipeline = new OrderPipeline(mockInventory, mockPayment);
        Order order = new Order(randomOrderId, "CUST-RANDOM", "ITEM-99", 5, randomAmount);

        String result = pipeline.processOrderAsync(order).get(2, TimeUnit.SECONDS);
        assertEquals("TXN_" + randomOrderId, result);
    }
}
