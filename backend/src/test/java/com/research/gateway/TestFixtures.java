package com.research.gateway;

import com.research.gateway.domain.ResearchReport;
import java.util.List;

public final class TestFixtures {

    private TestFixtures() {
    }

    public static ResearchReport report(String query) {
        return new ResearchReport(query, List.of(query),
                List.of(new ResearchReport.Finding(query, "A finding.", List.of(1), 0.8)),
                List.of(new ResearchReport.Source(1, "Title", "https://example.org", "text")),
                "# " + query, false,
                List.of(new ResearchReport.AgentTrace("planner", 1.5, "Planned 1")));
    }
}
