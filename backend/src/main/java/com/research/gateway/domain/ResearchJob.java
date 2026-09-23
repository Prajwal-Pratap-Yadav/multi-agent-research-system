package com.research.gateway.domain;

import java.time.Instant;
import java.util.UUID;

/**
 * Immutable snapshot of a research job. State transitions return new instances so jobs
 * can be safely shared across request and worker threads.
 */
public record ResearchJob(
        UUID id,
        String query,
        int maxSubQuestions,
        JobStatus status,
        Instant createdAt,
        Instant updatedAt,
        ResearchReport report,
        String error) {

    public static ResearchJob pending(String query, int maxSubQuestions, Instant now) {
        return new ResearchJob(UUID.randomUUID(), query, maxSubQuestions, JobStatus.PENDING,
                now, now, null, null);
    }

    public ResearchJob running(Instant now) {
        return new ResearchJob(id, query, maxSubQuestions, JobStatus.RUNNING, createdAt, now,
                null, null);
    }

    public ResearchJob completed(ResearchReport result, Instant now) {
        return new ResearchJob(id, query, maxSubQuestions, JobStatus.COMPLETED, createdAt, now,
                result, null);
    }

    public ResearchJob failed(String message, Instant now) {
        return new ResearchJob(id, query, maxSubQuestions, JobStatus.FAILED, createdAt, now,
                null, message);
    }
}
