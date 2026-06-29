package com.AlgoGym.backend.service;

import com.AlgoGym.backend.model.AIFeedback;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class AIFeedbackService {

    private static final Logger log = LoggerFactory.getLogger(AIFeedbackService.class);

    @Autowired
    private GroqLLMService groqLLMService;

    @Autowired
    private AIFeedbackRepository aiFeedbackRepository;

    @Autowired
    private ProblemRepository problemRepository;

    @Autowired
    private ObjectMapper objectMapper;


    public AIFeedback generateAndSave(Submission submission) {
        try {
            Problem problem = problemRepository.findById(submission.getProblemId())
                    .orElseThrow(() -> new RuntimeException("Problem not found"));

            String errorDetails = null;
            if (submission.getCompilationError() != null) {
                errorDetails = submission.getCompilationError();
            } else if (submission.getRuntimeError() != null) {
                errorDetails = submission.getRuntimeError();
            }

            Map<String, Object> aiResult = groqLLMService.analyzeError(
                    submission.getLanguageName(),
                    problem.getDescription(),
                    problem.getDifficulty(),
                    problem.getTags(),
                    submission.getSourceCode(),
                    submission.getVerdict(),
                    errorDetails,
                    submission.getFirstFailedInput(),
                    submission.getFirstFailedExpected(),
                    submission.getFirstFailedActual()
            );

            String tipsJson = objectMapper.writeValueAsString(aiResult.get("tips"));

            AIFeedback feedback = new AIFeedback();
            feedback.setSubmissionId(Long.parseLong(submission.getId().toString()));
            feedback.setErrorType((String) aiResult.get("error_type"));
            feedback.setExplanation((String) aiResult.get("explanation"));
            feedback.setTips(tipsJson);
            feedback.setLanguageName(submission.getLanguageName());

            return aiFeedbackRepository.save(feedback);

        } catch (Exception e) {
            log.error("Failed to generate AI feedback for submission {}: {}", submission.getId(), e.getMessage());
            return null;
        }
    }

    // Call this when reading AIFeedback from DB to convert tips back to a List
    public List<String> parseTips(String tipsJson) {
        try {
            return objectMapper.readValue(tipsJson,
                    objectMapper.getTypeFactory().constructCollectionType(List.class, String.class));
        } catch (Exception e) {
            return List.of();
        }
    }
    public AIFeedback getBySubmissionId(Long submissionId) {
        return aiFeedbackRepository.findBySubmissionId(submissionId).orElse(null);
    }
    public Map<String, Object> analyzeOnly(Submission submission) {
        try {
            Problem problem = problemRepository.findById(submission.getProblemId())
                    .orElseThrow(() -> new RuntimeException("Problem not found"));

            String errorDetails = submission.getCompilationError() != null
                    ? submission.getCompilationError()
                    : submission.getRuntimeError();

            return groqLLMService.analyzeError(
                    submission.getLanguageName(),
                    problem.getDescription(),
                    problem.getDifficulty(),
                    problem.getTags(),
                    submission.getSourceCode(),
                    submission.getVerdict(),
                    errorDetails,
                    submission.getFirstFailedInput(),
                    submission.getFirstFailedExpected(),
                    submission.getFirstFailedActual()
            );
        } catch (Exception e) {
            log.error("Failed to analyze run: {}", e.getMessage());
            return null;
        }
    }
}