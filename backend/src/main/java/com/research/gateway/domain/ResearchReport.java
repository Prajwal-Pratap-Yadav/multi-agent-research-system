package com.research.gateway.domain;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.util.List;

/** Report produced by the agent service (snake_case on the wire, mirrored verbatim). */
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ResearchReport(
        String query,
        List<String> subQuestions,
        List<Finding> findings,
        List<Source> sources,
        String reportMarkdown,
        boolean llmEnabled,
        List<AgentTrace> trace) {

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Finding(String subQuestion, String statement, List<Integer> sourceIds,
            double score) {
    }

    public record Source(int id, String title, String url, String content) {
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record AgentTrace(String agent, double durationMs, String summary) {
    }
}
