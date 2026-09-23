package com.research.gateway.api;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** Body of {@code POST /api/research}. */
public record CreateResearchRequest(
        @NotBlank(message = "query must not be blank")
        @Size(min = 3, max = 500, message = "query must be 3-500 characters")
        String query,
        @JsonProperty("maxSubQuestions")
        @Min(value = 1, message = "maxSubQuestions must be >= 1")
        @Max(value = 5, message = "maxSubQuestions must be <= 5")
        Integer maxSubQuestions) {

    public static final int DEFAULT_SUB_QUESTIONS = 3;

    public int maxSubQuestionsOrDefault() {
        return maxSubQuestions == null ? DEFAULT_SUB_QUESTIONS : maxSubQuestions;
    }
}
