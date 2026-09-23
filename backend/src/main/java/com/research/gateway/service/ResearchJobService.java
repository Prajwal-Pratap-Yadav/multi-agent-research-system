package com.research.gateway.service;

import com.research.gateway.client.AgentServiceClient;
import com.research.gateway.client.AgentServiceException;
import com.research.gateway.config.RequestIdFilter;
import com.research.gateway.config.ResearchProperties;
import com.research.gateway.domain.ResearchJob;
import java.time.Clock;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;

/**
 * Accepts research requests, runs them asynchronously against the agent service and keeps
 * job state in a bounded in-memory store (oldest jobs are evicted first).
 */
@Service
public class ResearchJobService {

    private static final Logger log = LoggerFactory.getLogger(ResearchJobService.class);

    private final AgentServiceClient client;
    private final ExecutorService executor;
    private final Clock clock;
    private final int maxStoredJobs;
    private final Map<UUID, ResearchJob> jobs = new ConcurrentHashMap<>();

    public ResearchJobService(AgentServiceClient client, ExecutorService researchExecutor,
            Clock clock, ResearchProperties props) {
        this.client = client;
        this.executor = researchExecutor;
        this.clock = clock;
        this.maxStoredJobs = props.maxStoredJobs();
    }

    /** Creates a job and schedules it; returns immediately with the PENDING snapshot. */
    public ResearchJob submit(String query, int maxSubQuestions) {
        ResearchJob job = ResearchJob.pending(query, maxSubQuestions, clock.instant());
        evictIfFull();
        jobs.put(job.id(), job);
        String requestId = MDC.get(RequestIdFilter.MDC_KEY);
        executor.execute(() -> execute(job.id(), requestId));
        log.info("Research job {} submitted", job.id());
        return job;
    }

    public ResearchJob get(UUID id) {
        ResearchJob job = jobs.get(id);
        if (job == null) {
            throw new JobNotFoundException(id);
        }
        return job;
    }

    /** Returns all known jobs, newest first. */
    public List<ResearchJob> list() {
        return jobs.values().stream()
                .sorted(Comparator.comparing(ResearchJob::createdAt).reversed())
                .toList();
    }

    void execute(UUID id, String requestId) {
        if (requestId != null) {
            MDC.put(RequestIdFilter.MDC_KEY, requestId);
        }
        try {
            ResearchJob job = jobs.computeIfPresent(id, (k, j) -> j.running(clock.instant()));
            if (job == null) {
                return;
            }
            long started = System.nanoTime();
            try {
                var report = client.research(job.query(), job.maxSubQuestions());
                jobs.computeIfPresent(id, (k, j) -> j.completed(report, clock.instant()));
                log.info("Research job {} completed in {} ms", id,
                        (System.nanoTime() - started) / 1_000_000);
            } catch (AgentServiceException e) {
                jobs.computeIfPresent(id, (k, j) -> j.failed(e.getMessage(), clock.instant()));
                log.error("Research job {} failed: {}", id, e.getMessage());
            } catch (RuntimeException e) {
                jobs.computeIfPresent(id, (k, j) -> j.failed("Internal error", clock.instant()));
                log.error("Research job {} failed unexpectedly", id, e);
            }
        } finally {
            MDC.remove(RequestIdFilter.MDC_KEY);
        }
    }

    private void evictIfFull() {
        while (jobs.size() >= maxStoredJobs) {
            jobs.values().stream()
                    .min(Comparator.comparing(ResearchJob::createdAt))
                    .ifPresent(oldest -> jobs.remove(oldest.id()));
        }
    }
}
