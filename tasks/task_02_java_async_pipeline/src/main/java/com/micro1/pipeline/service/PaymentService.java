package com.micro1.pipeline.service;

import java.math.BigDecimal;
import java.util.concurrent.CompletableFuture;

public interface PaymentService {
    CompletableFuture<String> processPayment(String orderId, BigDecimal amount);
}
