package com.research.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/** Entry point for the research gateway. */
@SpringBootApplication
@ConfigurationPropertiesScan
public class ResearchGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(ResearchGatewayApplication.class, args);
    }
}
