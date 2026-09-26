package com.micro1.pipeline.service;

import java.util.concurrent.CompletableFuture;

public interface InventoryService {
    CompletableFuture<Boolean> reserveInventory(String orderId, String itemId, int quantity);
    CompletableFuture<Void> releaseInventory(String orderId);
}
