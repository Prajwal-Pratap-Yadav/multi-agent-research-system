package com.research.gateway.client;

import com.research.gateway.config.RequestIdFilter;
import com.research.gateway.domain.ResearchReport;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

/** HTTP client for the Python agent service. */
@Component
public class AgentServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AgentServiceClient.class);

    private final RestClient restClient;

    public AgentServiceClient(RestClient agentRestClient) {
        this.restClient = agentRestClient;
    }

    /**
     * Runs the full agent pipeline synchronously.
     *
     * @throws AgentServiceException on transport errors, non-2xx responses or empty bodies
     */
    public ResearchReport research(String query, int maxSubQuestions) {
        try {
            ResearchReport report = restClient.post()
                    .uri("/research")
                    .contentType(MediaType.APPLICATION_JSON)
                    .headers(h -> {
                        String requestId = MDC.get(RequestIdFilter.MDC_KEY);
                        if (requestId != null) {
                            h.set(RequestIdFilter.HEADER, requestId);
                        }
                    })
                    .body(Map.of("query", query, "max_sub_questions", maxSubQuestions))
                    .retrieve()
                    .body(ResearchReport.class);
            if (report == null) {
                throw new AgentServiceException("Agent service returned an empty body");
            }
            return report;
        } catch (RestClientResponseException e) {
            log.warn("Agent service returned HTTP {}: {}", e.getStatusCode().value(),
                    e.getResponseBodyAsString());
            throw new AgentServiceException(
                    "Agent service returned HTTP " + e.getStatusCode().value(), e);
        } catch (RestClientException e) {
            throw new AgentServiceException("Agent service unreachable: " + e.getMessage(), e);
        }
    }
}
