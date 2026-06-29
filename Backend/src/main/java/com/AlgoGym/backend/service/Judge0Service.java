package com.AlgoGym.backend.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Service
public class Judge0Service {

    private static final Logger log = LoggerFactory.getLogger(Judge0Service.class);

    private final RestTemplate restTemplate;

    @Value("${judge0.api.url}")
    private String apiUrl;

    @Value("${judge0.api.key}")
    private String apiKey;

    @Value("${judge0.api.host}")
    private String apiHost;

    public Judge0Service(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Submit code for execution
     *
     * @param sourceCode The code to execute
     * @param languageId Judge0 language ID (71=Python, 62=Java, etc.)
     * @param stdin Input for the program
     * @return Submission token for status checking
     */
    public String submitCode(
            String sourceCode,
            Integer languageId,
            String stdin,
            Double timeLimitSeconds,
            Double memoryLimitKb
    ) {
        String url = apiUrl + "/submissions?base64_encoded=true&wait=false";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-RapidAPI-Key", apiKey);
        headers.set("X-RapidAPI-Host", apiHost);

        Map<String, Object> body = new HashMap<>();
        // ← encode source code and stdin as base64 before sending
        body.put("source_code", Base64.getEncoder().encodeToString(sourceCode.getBytes()));
        body.put("language_id", languageId);
        body.put("stdin", Base64.getEncoder().encodeToString(
                (stdin != null ? stdin : "").getBytes()
        ));

        if (timeLimitSeconds != null) body.put("cpu_time_limit", timeLimitSeconds);
        if (memoryLimitKb != null)    body.put("memory_limit", memoryLimitKb);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
                url, HttpMethod.POST, request, Map.class
        );

        return (String) response.getBody().get("token");
    }
    /**
     * Get submission result by token
     *
     * @param token Submission token from submitCode()
     * @return Submission details including status, output, errors
     */
    public Map<String, Object> getSubmission(String token) {
        try {
            String url = apiUrl + "/submissions/" + token + "?base64_encoded=true";

            HttpHeaders headers = createHeaders();
            HttpEntity<Void> request = new HttpEntity<>(headers);

            ResponseEntity<Map> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    request,
                    Map.class
            );

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                return response.getBody();
            }

            throw new RuntimeException("Failed to get submission. Status: " + response.getStatusCode());

        } catch (Exception e) {
            log.error("Error getting submission: {}", e.getMessage());
            throw new RuntimeException("Error getting submission: " + e.getMessage(), e);
        }
    }

    /**
     * Wait for submission to complete and return final result
     *
     * @param token Submission token
     * @return Final submission result
     * @throws InterruptedException if waiting is interrupted
     */
    public Map<String, Object> waitForResult(String token) throws InterruptedException {
        int maxAttempts = 20; // Max 10 seconds (20 * 500ms)
        int attempts = 0;

        while (attempts < maxAttempts) {
            Map<String, Object> result = getSubmission(token);

            // Get status
            Map<String, Object> status = (Map<String, Object>) result.get("status");
            Integer statusId = (Integer) status.get("id");
            String statusDescription = (String) status.get("description");

            log.info("Attempt {}/{}: Status = {} ({})",
                    attempts + 1, maxAttempts, statusId, statusDescription);

            // Status ID meanings:
            // 1, 2 = In Queue / Processing (wait)
            // 3+ = Finished (accepted, wrong answer, error, etc.)
            if (statusId > 2) {
                log.info("Execution completed: {}", statusDescription);
                return result;
            }

            Thread.sleep(500); // Wait 500ms before checking again
            attempts++;
        }

        throw new RuntimeException("Timeout: Submission took too long to execute");
    }

    /* Create HTTP headers for RapidAPI requests */
    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-RapidAPI-Key", apiKey);
        headers.set("X-RapidAPI-Host", apiHost);
        return headers;
    }


}