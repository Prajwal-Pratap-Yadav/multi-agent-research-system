package com.research.gateway.api;

import static org.hamcrest.Matchers.containsString;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.research.gateway.config.RequestIdFilter;
import com.research.gateway.domain.ResearchJob;
import com.research.gateway.service.JobNotFoundException;
import com.research.gateway.service.ResearchJobService;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ResearchController.class)
@Import(RequestIdFilter.class)
class ResearchControllerTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private ResearchJobService service;

    private final ResearchJob job = ResearchJob.pending("quantum computing", 3, Instant.EPOCH);

    @Test
    void createReturns202WithLocation() throws Exception {
        when(service.submit("quantum computing", 3)).thenReturn(job);

        mvc.perform(post("/api/research").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"  quantum computing \"}"))
                .andExpect(status().isAccepted())
                .andExpect(header().string("Location", "/api/research/" + job.id()))
                .andExpect(header().exists(RequestIdFilter.HEADER))
                .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void createRejectsInvalidInput() throws Exception {
        mvc.perform(post("/api/research").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"ab\",\"maxSubQuestions\":9}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Validation failed"))
                .andExpect(jsonPath("$.detail", containsString("maxSubQuestions must be <= 5")))
                .andExpect(jsonPath("$.detail", containsString("query must be 3-500")));
        verify(service, never()).submit(anyString(), anyInt());
    }

    @Test
    void createRejectsMalformedJson() throws Exception {
        mvc.perform(post("/api/research").contentType(MediaType.APPLICATION_JSON)
                        .content("{not json"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Malformed request"));
    }

    @Test
    void getReturnsJob() throws Exception {
        when(service.get(job.id())).thenReturn(job);

        mvc.perform(get("/api/research/{id}", job.id()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.query").value("quantum computing"));
    }

    @Test
    void getUnknownJobReturns404() throws Exception {
        UUID id = UUID.randomUUID();
        when(service.get(id)).thenThrow(new JobNotFoundException(id));

        mvc.perform(get("/api/research/{id}", id))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Job not found"));
    }

    @Test
    void getWithInvalidIdReturns400() throws Exception {
        mvc.perform(get("/api/research/not-a-uuid")).andExpect(status().isBadRequest());
    }

    @Test
    void listReturnsJobs() throws Exception {
        when(service.list()).thenReturn(List.of(job));

        mvc.perform(get("/api/research"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(job.id().toString()));
    }

    @Test
    void propagatesValidIncomingRequestId() throws Exception {
        when(service.list()).thenReturn(List.of());

        mvc.perform(get("/api/research").header(RequestIdFilter.HEADER, "abc-123"))
                .andExpect(header().string(RequestIdFilter.HEADER, "abc-123"));
    }
}
