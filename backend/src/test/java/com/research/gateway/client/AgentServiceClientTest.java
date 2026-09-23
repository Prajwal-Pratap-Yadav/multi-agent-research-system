package com.research.gateway.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.research.gateway.domain.ResearchReport;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class AgentServiceClientTest {

    private MockRestServiceServer server;
    private AgentServiceClient client;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://agents");
        server = MockRestServiceServer.bindTo(builder).build();
        client = new AgentServiceClient(builder.build());
    }

    @Test
    void mapsSnakeCaseResponse() {
        server.expect(requestTo("http://agents/research"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().json("{\"query\":\"ai\",\"max_sub_questions\":2}"))
                .andRespond(withSuccess("""
                        {"query":"ai","sub_questions":["ai"],"findings":[{"sub_question":"ai",
                        "statement":"s","source_ids":[1],"score":0.5}],"sources":[{"id":1,
                        "title":"t","url":"u","content":"c"}],"report_markdown":"# ai",
                        "llm_enabled":true,"trace":[{"agent":"planner","duration_ms":2.0,
                        "summary":"ok"}]}
                        """, MediaType.APPLICATION_JSON));

        ResearchReport report = client.research("ai", 2);

        assertThat(report.subQuestions()).containsExactly("ai");
        assertThat(report.findings().get(0).sourceIds()).containsExactly(1);
        assertThat(report.reportMarkdown()).isEqualTo("# ai");
        assertThat(report.llmEnabled()).isTrue();
        assertThat(report.trace().get(0).durationMs()).isEqualTo(2.0);
        server.verify();
    }

    @Test
    void wrapsHttpErrors() {
        server.expect(requestTo("http://agents/research")).andRespond(withServerError());

        assertThatThrownBy(() -> client.research("ai", 2))
                .isInstanceOf(AgentServiceException.class)
                .hasMessageContaining("500");
    }
}
