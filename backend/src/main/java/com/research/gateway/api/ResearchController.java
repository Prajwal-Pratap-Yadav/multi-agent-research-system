package com.research.gateway.api;

import com.research.gateway.domain.ResearchJob;
import com.research.gateway.service.ResearchJobService;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Public REST API for submitting and polling research jobs. */
@RestController
@RequestMapping("/api/research")
public class ResearchController {

    private final ResearchJobService service;

    public ResearchController(ResearchJobService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<ResearchJob> create(@Valid @RequestBody CreateResearchRequest request) {
        ResearchJob job = service.submit(request.query().strip(),
                request.maxSubQuestionsOrDefault());
        return ResponseEntity.accepted()
                .location(URI.create("/api/research/" + job.id()))
                .body(job);
    }

    @GetMapping("/{id}")
    public ResearchJob get(@PathVariable UUID id) {
        return service.get(id);
    }

    @GetMapping
    public List<ResearchJob> list() {
        return service.list();
    }
}
