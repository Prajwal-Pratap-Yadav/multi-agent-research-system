package com.research.gateway.config;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

/** Tuning for the asynchronous job runner. */
@Validated
@ConfigurationProperties(prefix = "research")
public record ResearchProperties(
        @Min(1) @Max(64) int workerThreads,
        @Min(1) int maxStoredJobs) {
}
