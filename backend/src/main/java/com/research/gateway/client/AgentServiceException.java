package com.research.gateway.client;

/** Raised when the agent service is unreachable or responds with an error. */
public class AgentServiceException extends RuntimeException {

    public AgentServiceException(String message, Throwable cause) {
        super(message, cause);
    }

    public AgentServiceException(String message) {
        super(message);
    }
}
