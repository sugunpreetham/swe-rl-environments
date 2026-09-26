package com.micro1.pipeline;

import com.micro1.pipeline.model.Order;
import com.micro1.pipeline.service.InventoryService;
import com.micro1.pipeline.service.PaymentService;

import java.util.concurrent.*;

public class OrderPipeline {

    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final Executor executor;
    private final long paymentTimeoutMs;

    public OrderPipeline(InventoryService inventoryService, PaymentService paymentService, Executor executor, long paymentTimeoutMs) {
        this.inventoryService = inventoryService;
        this.paymentService = paymentService;
        this.executor = executor != null ? executor : ForkJoinPool.commonPool();
        this.paymentTimeoutMs = paymentTimeoutMs > 0 ? paymentTimeoutMs : 1500;
    }

    public OrderPipeline(InventoryService inventoryService, PaymentService paymentService) {
        this(inventoryService, paymentService, ForkJoinPool.commonPool(), 1500);
    }

    /**
     * Executes the order pipeline asynchronously.
     * Guaranteed Saga compensation: If payment fails or times out after inventory reservation,
     * the reserved inventory is asynchronously rolled back before completing exceptionally.
     */
    public CompletableFuture<String> processOrderAsync(Order order) {
        if (order == null) {
            return CompletableFuture.failedFuture(new IllegalArgumentException("Order cannot be null"));
        }

        // Step 1: Asynchronous Inventory Reservation
        return inventoryService.reserveInventory(order.id(), order.itemId(), order.quantity())
            .thenComposeAsync(reserved -> {
                if (!Boolean.TRUE.equals(reserved)) {
                    throw new IllegalStateException("Insufficient inventory for order: " + order.id());
                }

                // Step 2: Payment processing with bounded timeout
                return paymentService.processPayment(order.id(), order.amount())
                    .orTimeout(paymentTimeoutMs, TimeUnit.MILLISECONDS)
                    .handleAsync((paymentTxId, paymentError) -> {
                        if (paymentError != null) {
                            // Step 3 (Compensation): Payment failed/timed out -> rollback inventory
                            inventoryService.releaseInventory(order.id());
                            if (paymentError instanceof CompletionException ce) {
                                throw ce;
                            }
                            throw new CompletionException(paymentError);
                        }
                        return paymentTxId;
                    }, executor);
            }, executor);
    }
}
