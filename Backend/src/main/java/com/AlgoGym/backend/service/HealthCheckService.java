package com.AlgoGym.backend.service;

import com.AlgoGym.backend.repository.UserRepository;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Service
@RequiredArgsConstructor
public class HealthCheckService {

    private static final long DEGRADED_THRESHOLD_MS = 1000L;

    private final UserRepository userRepository;
    private final RestTemplate healthRestTemplate = createHealthRestTemplate();

    @Value("${judge0.api.url}")
    private String judge0ApiUrl;

    @Value("${judge0.api.key}")
    private String judge0ApiKey;

    @Value("${judge0.api.host}")
    private String judge0ApiHost;

    @Value("${groq.api.url}")
    private String groqApiUrl;

    @Value("${groq.api.key}")
    private String groqApiKey;

    public HealthCheckResult checkDatabase() {
        long start = System.currentTimeMillis();
        try {
            userRepository.count();
            return new HealthCheckResult("ONLINE", System.currentTimeMillis() - start);
        } catch (Exception e) {
            return new HealthCheckResult("OFFLINE", -1L);
        }
    }

    public HealthCheckResult checkJudge0() {
        long start = System.currentTimeMillis();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("X-RapidAPI-Key", judge0ApiKey);
            headers.set("X-RapidAPI-Host", judge0ApiHost);

            HttpEntity<Void> request = new HttpEntity<>(headers);
            ResponseEntity<String> response = healthRestTemplate.exchange(
                    judge0ApiUrl + "/about",
                    HttpMethod.GET,
                    request,
                    String.class
            );

            long latency = System.currentTimeMillis() - start;
            if (response.getStatusCode() == HttpStatus.OK) {
                String status = latency > DEGRADED_THRESHOLD_MS ? "DEGRADED" : "ONLINE";
                return new HealthCheckResult(status, latency);
            }
            return new HealthCheckResult("OFFLINE", -1L);
        } catch (Exception e) {
            return new HealthCheckResult("OFFLINE", -1L);
        }
    }

    public HealthCheckResult checkGroq() {
        long start = System.currentTimeMillis();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setBearerAuth(groqApiKey);

            HttpEntity<Void> request = new HttpEntity<>(headers);
            ResponseEntity<String> response = healthRestTemplate.exchange(
                    resolveGroqHealthUrl(),
                    HttpMethod.GET,
                    request,
                    String.class
            );

            long latency = System.currentTimeMillis() - start;
            if (response.getStatusCode() == HttpStatus.OK) {
                String status = latency > DEGRADED_THRESHOLD_MS ? "DEGRADED" : "ONLINE";
                return new HealthCheckResult(status, latency);
            }
            return new HealthCheckResult("OFFLINE", -1L);
        } catch (Exception e) {
            return new HealthCheckResult("OFFLINE", -1L);
        }
    }

    private String resolveGroqHealthUrl() {
        if (groqApiUrl.endsWith("/chat/completions")) {
            return groqApiUrl.replace("/chat/completions", "/models");
        }
        return groqApiUrl;
    }

    private static RestTemplate createHealthRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(5));
        factory.setReadTimeout(Duration.ofSeconds(5));
        return new RestTemplate(factory);
    }

    @Getter
    public static class HealthCheckResult {
        private final String status;
        private final Long latencyMs;

        public HealthCheckResult(String status, Long latencyMs) {
            this.status = status;
            this.latencyMs = latencyMs;
        }
    }
}
