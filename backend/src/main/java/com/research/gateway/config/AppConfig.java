package com.research.gateway.config;

import java.net.http.HttpClient;
import java.time.Clock;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.boot.http.client.ClientHttpRequestFactoryBuilder;
import org.springframework.boot.http.client.ClientHttpRequestFactorySettings;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/** Infrastructure beans: HTTP client for the agent service and the job executor. */
@Configuration
public class AppConfig {

    @Bean
    RestClient agentRestClient(RestClient.Builder builder, AgentServiceProperties props) {
        var settings = ClientHttpRequestFactorySettings.defaults()
                .withConnectTimeout(props.connectTimeout())
                .withReadTimeout(props.readTimeout());
        return builder
                .baseUrl(props.baseUrl())
                .requestFactory(ClientHttpRequestFactoryBuilder.jdk()
                        // uvicorn rejects the h2c upgrade the JDK client attempts by default
                        .withHttpClientCustomizer(c -> c.version(HttpClient.Version.HTTP_1_1))
                        .build(settings))
                .build();
    }

    @Bean
    Clock clock() {
        return Clock.systemUTC();
    }

    @Bean(destroyMethod = "shutdown")
    ExecutorService researchExecutor(ResearchProperties props) {
        var counter = new AtomicInteger();
        return Executors.newFixedThreadPool(props.workerThreads(), runnable -> {
            var thread = new Thread(runnable, "research-worker-" + counter.incrementAndGet());
            thread.setDaemon(true);
            return thread;
        });
    }
}
