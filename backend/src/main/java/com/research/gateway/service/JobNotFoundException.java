package com.research.gateway.service;

import java.util.UUID;

/** Raised when a job ID does not exist (or has been evicted). */
public class JobNotFoundException extends RuntimeException {

    public JobNotFoundException(UUID id) {
        super("Research job " + id + " not found");
    }
}
