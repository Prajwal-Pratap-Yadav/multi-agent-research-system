package com.research.gateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.research.gateway.TestFixtures;
import com.research.gateway.client.AgentServiceClient;
import com.research.gateway.client.AgentServiceException;
import com.research.gateway.config.ResearchProperties;
import com.research.gateway.domain.JobStatus;
import com.research.gateway.domain.ResearchJob;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.AbstractExecutorService;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class ResearchJobServiceTest {

    /** Executor that queues tasks so tests control when they run. */
    static final class ManualExecutor extends AbstractExecutorService {
        final List<Runnable> tasks = new ArrayList<>();

        @Override public void execute(Runnable command) { tasks.add(command); }
        void runAll() { tasks.forEach(Runnable::run); tasks.clear(); }
        @Override public void shutdown() { }
        @Override public List<Runnable> shutdownNow() { return List.of(); }
        @Override public boolean isShutdown() { return false; }
        @Override public boolean isTerminated() { return false; }
        @Override public boolean awaitTermination(long t, TimeUnit u) { return true; }
    }

    private final AgentServiceClient client = mock(AgentServiceClient.class);
    private final ManualExecutor executor = new ManualExecutor();
    private MutableClock clock;
    private ResearchJobService service;

    @BeforeEach
    void setUp() {
        clock = new MutableClock(Instant.parse("2026-01-01T00:00:00Z"));
        service = new ResearchJobService(client, executor, clock, new ResearchProperties(2, 2));
    }

    @Test
    void submitReturnsPendingJobAndCompletesAsynchronously() {
        when(client.research("quantum", 3)).thenReturn(TestFixtures.report("quantum"));

        ResearchJob job = service.submit("quantum", 3);
        assertThat(job.status()).isEqualTo(JobStatus.PENDING);

        clock.advance(Duration.ofSeconds(5));
        executor.runAll();

        ResearchJob done = service.get(job.id());
        assertThat(done.status()).isEqualTo(JobStatus.COMPLETED);
        assertThat(done.report().query()).isEqualTo("quantum");
        assertThat(done.updatedAt()).isAfter(done.createdAt());
    }

    @Test
    void agentFailureMarksJobFailed() {
        when(client.research("x y z", 2)).thenThrow(new AgentServiceException("down"));

        ResearchJob job = service.submit("x y z", 2);
        executor.runAll();

        ResearchJob failed = service.get(job.id());
        assertThat(failed.status()).isEqualTo(JobStatus.FAILED);
        assertThat(failed.error()).isEqualTo("down");
        assertThat(failed.report()).isNull();
    }

    @Test
    void unexpectedErrorDoesNotLeakDetails() {
        when(client.research("boom", 1)).thenThrow(new IllegalStateException("secret"));

        ResearchJob job = service.submit("boom", 1);
        executor.runAll();

        assertThat(service.get(job.id()).error()).isEqualTo("Internal error");
    }

    @Test
    void unknownJobThrows() {
        assertThatThrownBy(() -> service.get(UUID.randomUUID()))
                .isInstanceOf(JobNotFoundException.class);
    }

    @Test
    void listIsNewestFirstAndOldestJobsAreEvicted() {
        ResearchJob first = service.submit("first", 1);
        clock.advance(Duration.ofSeconds(1));
        ResearchJob second = service.submit("second", 1);
        clock.advance(Duration.ofSeconds(1));
        ResearchJob third = service.submit("third", 1);

        assertThat(service.list()).extracting(ResearchJob::id)
                .containsExactly(third.id(), second.id());
        assertThatThrownBy(() -> service.get(first.id()))
                .isInstanceOf(JobNotFoundException.class);
    }

    static final class MutableClock extends Clock {
        private Instant now;

        MutableClock(Instant now) { this.now = now; }
        void advance(Duration d) { now = now.plus(d); }
        @Override public ZoneOffset getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(java.time.ZoneId zone) { return this; }
        @Override public Instant instant() { return now; }
    }
}
