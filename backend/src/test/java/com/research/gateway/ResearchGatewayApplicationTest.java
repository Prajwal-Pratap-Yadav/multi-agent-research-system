package com.research.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ResearchGatewayApplicationTest {

    @Autowired
    private TestRestTemplate rest;

    @Test
    void contextLoadsAndHealthIsUp() {
        assertThat(rest.getForObject("/actuator/health", String.class)).contains("UP");
    }
}
