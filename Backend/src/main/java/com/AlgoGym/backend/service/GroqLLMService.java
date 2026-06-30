package com.AlgoGym.backend.service;

import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Service
public class GroqLLMService {

    private static final Logger log = LoggerFactory.getLogger(GroqLLMService.class);

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${groq.api.key}")
    private String apiKey;

    @Value("${groq.api.url}")
    private String apiUrl;

    public GroqLLMService(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> analyzeError(
            String languageName,
            String problemDescription,
            String difficulty,
            List<String> tags,
            String sourceCode,
            String verdict,
            String errorDetails,
            String firstFailedInput,
            String firstFailedExpected,
            String firstFailedActual
    ) {

        String errorType = switch (verdict) {
            case "COMPILATION_ERROR"    -> "SYNTAX_ERROR";
            case "RUNTIME_ERROR"        -> "RUNTIME_ERROR";
            case "TIME_LIMIT_EXCEEDED"  -> "OPTIMIZATION";
            case "MEMORY_LIMIT_EXCEEDED"-> "OPTIMIZATION";
            default                     -> "LOGIC_ERROR"; // WRONG_ANSWER
        };


        String systemPrompt = """
You are a cheerful and friendly AI programming coach for a competitive programming platform.

You will receive:
- the problem description
- the difficulty of the problem and its tags
- the user's code
- the submission verdict
- the first failed test case (input, expected output, actual output)
- a compiler/runtime error (if any)

Your goal is to help the user understand WHY their code failed and give hints to fix it, without giving the full solution.

Your Vibe:
- Use "We" and "Our" frequently (e.g., "Our code," "Let's look at..."). It’s a team effort!
- Be encouraging and friendly: celebrate progress, even small steps.
- Use motivational phrases like "Good job!", "Almost there!", "Let’s try…", "Nice attempt!", "We can fix this!".
- Avoid starting every response with “Hey!”; keep it varied and natural.

How to reason:
1. Identify the key requirement or rule in the problem.
2. Analyze the code and the failed test case to find the likely mistake.
3. Use the compiler/runtime error only as supporting context.
4. Think step by step internally, but do not show your reasoning — only produce the explanation and tips, keeping them at the same level of the problem difficulty.

Rules:
- Speak directly to the user in a cheerful, supportive tone.
- Focus on helping the user notice mistakes and think for themselves.
- Only give guidance on what the user has actually tried in their code.
- Never give the full solution.
- Give 1–2 small, actionable hints that guide the user to debug, correct, or continue their own approach.
- If the user's code is empty, placeholder, or stuck (infinite loop), do NOT suggest algorithms, strategies, or data structures. Only guide them to start writing their own logic (reading input, storing values, printing debug info).
- Avoid sounding harsh, critical, or bossy. Think of yourself as a fun gym buddy for their code.

Output format (strict JSON):
{
  "explanation": "Explain the main mistake in 1–2 sentences, speaking directly to the user in a friendly way.",
  "tips": ["Short, cheerful hint 1", "Short, cheerful hint 2"]
}

Example (unrelated problem):

Problem:
Return the index of the largest number in an array.

User Code:
The code sorts the array and returns the last element.

Output:
{
  "explanation": "Looks like we’re returning the largest value itself, but we actually need the index of that value in the original array.",
  "tips": [
    "Keep track of the position of the largest element as you scan the array.",
    "No need to sort if we only want the max index."
  ]
}

Now generate the response for the user's submission as AlgoGym Buddy.
""";

        //for the LLM only not the userrr
        StringBuilder failureInfo = new StringBuilder();
        failureInfo.append("Verdict: ").append(verdict).append("\n");
        if (errorDetails != null && !errorDetails.isBlank()) {
            failureInfo.append("Error message:\n").append(errorDetails).append("\n");
        }
        if (firstFailedInput != null) {
            failureInfo.append("Failed on input:\n").append(firstFailedInput).append("\n");
            failureInfo.append("Expected output: ").append(firstFailedExpected).append("\n");
            if (firstFailedActual != null) {
                failureInfo.append("Actual output: ").append(firstFailedActual).append("\n");
            }
        }

        String userPrompt = String.format("""
    Language: %s
    Problem Difficulty: %s
    Problem Tags: %s
    
    Problem Description:
    %s
    
    User's Code:
    %s
    
    What went wrong:
    %s
    """, languageName, difficulty, tags, problemDescription, sourceCode, failureInfo);

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(apiKey);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "llama-3.3-70b-versatile");
            requestBody.put("temperature", 0.2);
            requestBody.put("response_format", Map.of("type", "json_object"));
            requestBody.put("messages", List.of(
                    Map.of("role", "system", "content", systemPrompt),
                    Map.of("role", "user",   "content", userPrompt)
            ));

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            ResponseEntity<Map> response = restTemplate.exchange(apiUrl, HttpMethod.POST, request, Map.class);

            Map<String, Object> body = response.getBody();
            List<Map<String, Object>> choices = (List<Map<String, Object>>) body.get("choices");
            Map<String, Object> message = (Map<String, Object>) choices.get(0).get("message");
            String content = (String) message.get("content");

            JsonNode parsed = objectMapper.readTree(content);

            List<String> tips = new ArrayList<>();
            if (parsed.has("tips") && parsed.get("tips").isArray()) {
                for (JsonNode tip : parsed.get("tips")) {
                    tips.add(tip.asText());
                }
            }

            return Map.of(
                    "error_type",   errorType,
                    "explanation",  parsed.get("explanation").asText(""),
                    "tips",         tips
            );

        } catch (Exception e) {
            log.error("Groq API error: {}", e.getMessage());
            return Map.of(
                    "error_type",  errorType,
                    "explanation", "Unable to analyze the error at this time.",
                    "tips",        List.of("Review your code carefully.", "Look carefully at the problem description and input format")
            );
        }
    }

    /**
     * Personalized progress insight from the user's latest submission and top weak KCs.
     */
    public String generateProgressInsight(
            Submission latest,
            Problem problem,
            List<String> weakTopicsWithMastery
    ) {
        if (latest == null && (weakTopicsWithMastery == null || weakTopicsWithMastery.isEmpty())) {
            return "Keep solving problems to unlock personalized AI insights.";
        }

        String systemPrompt = """
You are AlgoGym Buddy, a friendly competitive programming coach.

Given the user's most recent submission and their top weak knowledge areas (with mastery %), write ONE short personalized insight.

Rules:
- 2–3 sentences, plain text only (no markdown, no bullet points).
- Start immediately with the insight. Do NOT use introductory phrases like "Congratulations", "You've just", "Great job", or "Now it's time".
- If the last submission is relevant, mention it naturally in one short clause (e.g., "Although your last submission was accepted...") without making it the focus.
- Focus primarily on the user's weakest topics and what they should practice next.
- Recommend practicing easy or medium problems on the weakest topics.
- Be encouraging, concise, and specific.
- Do not invent problems, statistics, or achievements that were not provided.
- Use "you" and keep a warm, motivating tone.
""";

        StringBuilder userPrompt = new StringBuilder();

        if (latest != null) {
            userPrompt.append("Latest submission:\n");
            userPrompt.append("- Problem: ").append(problemTitle(problem, latest.getProblemId())).append("\n");
            if (problem != null) {
                userPrompt.append("- Difficulty: ").append(resolveDifficulty(problem)).append("\n");
                if (problem.getTags() != null && !problem.getTags().isEmpty()) {
                    userPrompt.append("- Tags: ").append(String.join(", ", problem.getTags())).append("\n");
                }
            }
            userPrompt.append("- Verdict: ").append(latest.getVerdict()).append("\n");
            userPrompt.append("- Language: ").append(
                    latest.getLanguageName() != null ? latest.getLanguageName() : "unknown"
            ).append("\n");
            if (latest.getPassedTests() != null && latest.getTotalTests() != null) {
                userPrompt.append("- Tests passed: ")
                        .append(latest.getPassedTests())
                        .append("/")
                        .append(latest.getTotalTests())
                        .append("\n");
            }
            String code = latest.getSourceCode();
            if (code != null && !code.isBlank()) {
                userPrompt.append("- Code snippet (truncated):\n```\n")
                        .append(truncate(code, 1500))
                        .append("\n```\n");
            }
        } else {
            userPrompt.append("Latest submission: none on record.\n");
        }

        userPrompt.append("\nTop weak topics (weakest first):\n");
        if (weakTopicsWithMastery == null || weakTopicsWithMastery.isEmpty()) {
            userPrompt.append("- (not available)\n");
        } else {
            for (int i = 0; i < weakTopicsWithMastery.size(); i++) {
                userPrompt.append(i + 1).append(". ").append(weakTopicsWithMastery.get(i)).append("\n");
            }
        }

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(apiKey);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "llama-3.3-70b-versatile");
            requestBody.put("temperature", 0.4);
            requestBody.put("max_tokens", 220);
            requestBody.put("messages", List.of(
                    Map.of("role", "system", "content", systemPrompt),
                    Map.of("role", "user", "content", userPrompt.toString())
            ));

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            ResponseEntity<Map> response = restTemplate.exchange(apiUrl, HttpMethod.POST, request, Map.class);

            Map<String, Object> body = response.getBody();
            if (body == null) {
                return fallbackProgressInsight(latest, weakTopicsWithMastery);
            }
            List<Map<String, Object>> choices = (List<Map<String, Object>>) body.get("choices");
            if (choices == null || choices.isEmpty()) {
                return fallbackProgressInsight(latest, weakTopicsWithMastery);
            }
            Map<String, Object> message = (Map<String, Object>) choices.get(0).get("message");
            String content = message != null ? (String) message.get("content") : null;
            if (content == null || content.isBlank()) {
                return fallbackProgressInsight(latest, weakTopicsWithMastery);
            }
            return content.trim();

        } catch (Exception e) {
            log.error("Groq progress insight error: {}", e.getMessage());
            return fallbackProgressInsight(latest, weakTopicsWithMastery);
        }
    }

    private String fallbackProgressInsight(Submission latest, List<String> weakTopics) {
        StringBuilder sb = new StringBuilder();
        if (latest != null) {
            sb.append("Your last submission was ")
                    .append(latest.getVerdict().replace('_', ' ').toLowerCase(Locale.ROOT))
                    .append(". ");
        }
        if (weakTopics != null && !weakTopics.isEmpty()) {
            sb.append("Focus next on ")
                    .append(String.join(", ", weakTopics.subList(0, Math.min(3, weakTopics.size()))))
                    .append(" — your weakest areas right now.");
        } else {
            sb.append("Keep practicing consistently to build momentum.");
        }
        return sb.toString().trim();
    }

    private static String problemTitle(Problem problem, String problemId) {
        if (problem != null && problem.getTitle() != null && !problem.getTitle().isBlank()) {
            return problem.getTitle();
        }
        return problemId != null ? problemId : "Unknown";
    }

    private static String resolveDifficulty(Problem problem) {
        if (problem.getDifficulty() != null && !problem.getDifficulty().isBlank()) {
            return problem.getDifficulty().toUpperCase(Locale.ROOT);
        }
        Long rating = problem.getRating();
        if (rating == null) {
            return "MEDIUM";
        }
        if (rating < 1200) {
            return "EASY";
        }
        if (rating < 1600) {
            return "MEDIUM";
        }
        return "HARD";
    }

    private static String truncate(String text, int maxLen) {
        if (text.length() <= maxLen) {
            return text;
        }
        return text.substring(0, maxLen) + "\n... (truncated)";
    }
}