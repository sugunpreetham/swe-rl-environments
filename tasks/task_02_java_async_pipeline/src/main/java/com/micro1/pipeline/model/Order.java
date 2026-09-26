package com.micro1.pipeline.model;

import java.math.BigDecimal;

public record Order(
    String id,
    String customerId,
    String itemId,
    int quantity,
    BigDecimal amount
) {
    public Order {
        if (id == null || id.isBlank()) throw new IllegalArgumentException("Order ID cannot be empty");
        if (quantity <= 0) throw new IllegalArgumentException("Quantity must be positive");
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }
}
