package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.CodeSubmissionRequest;
import com.AlgoGym.backend.dto.SubmissionResponse;
import com.AlgoGym.backend.model.AIFeedback;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.service.AIFeedbackService;
import com.AlgoGym.backend.service.CodeExecutionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/code")
@CrossOrigin(origins = "*")
public class CodeExecutionController {

    @Autowired
    private CodeExecutionService codeExecutionService;

    @Autowired
    private AIFeedbackService aiFeedbackService;

    @Autowired
    private UserRepository userRepository;  // ← ADD THIS

    @PostMapping("/submit")
    public ResponseEntity<SubmissionResponse> submitCode(
            @RequestBody CodeSubmissionRequest request,
            Authentication authentication  // ← ADD THIS
    ) {
        try {
            // Extract user ID from JWT authentication
            String userId = getUserIdFromAuth(authentication);

            Submission submission = codeExecutionService.executeCode(
                    userId,  // ← USE AUTHENTICATED USER ID
                    request.getProblemId(),
                    request.getSourceCode(),
                    request.getLanguageId(),
                    request.getLanguageName()
            );

            SubmissionResponse response = convertToResponse(submission);

            if (!"ACCEPTED".equals(submission.getVerdict())) {
                AIFeedback feedback = aiFeedbackService.getBySubmissionId(
                        Long.parseLong(submission.getId().toString())
                );
                if (feedback != null) {
                    response.setAiErrorType(feedback.getErrorType());
                    response.setAiExplanation(feedback.getExplanation());
                    response.setAiTips(aiFeedbackService.parseTips(feedback.getTips()));
                }
            }

            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/run")
    public ResponseEntity<SubmissionResponse> runCode(
            @RequestBody CodeSubmissionRequest request,
            Authentication authentication  // ← ADD THIS
    ) {
        try {
            // Extract user ID from JWT authentication
            String userId = getUserIdFromAuth(authentication);

            Submission submission = codeExecutionService.runCode(
                    userId,  // ← USE AUTHENTICATED USER ID
                    request.getProblemId(),
                    request.getSourceCode(),
                    request.getLanguageId(),
                    request.getLanguageName()
            );

            SubmissionResponse response = convertToResponse(submission);

            // Analyze don't save
            if (!"ACCEPTED".equals(submission.getVerdict())) {
                Map<String, Object> aiResult = aiFeedbackService.analyzeOnly(submission);
                if (aiResult != null) {
                    response.setAiErrorType((String) aiResult.get("error_type"));
                    response.setAiExplanation((String) aiResult.get("explanation"));
                    response.setAiTips((List<String>) aiResult.get("tips"));
                }
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // ← ADD THIS HELPER METHOD
    private String getUserIdFromAuth(Authentication authentication) {
        String username = authentication.getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return user.getId();
    }

    private SubmissionResponse convertToResponse(Submission submission) {
        SubmissionResponse response = new SubmissionResponse();
        response.setSubmissionId(submission.getId());
        response.setVerdict(submission.getVerdict());
        response.setPassedTests(submission.getPassedTests());
        response.setTotalTests(submission.getTotalTests());
        response.setExecutionTimeMs(submission.getExecutionTimeMs());
        response.setMemoryUsedKb(submission.getMemoryUsedKb());
        response.setTestResults(submission.getTestResults());
        response.setFirstFailedInput(submission.getFirstFailedInput());
        response.setFirstFailedExpected(submission.getFirstFailedExpected());
        response.setFirstFailedActual(submission.getFirstFailedActual());
        response.setCompilationError(submission.getCompilationError());
        response.setRuntimeError(submission.getRuntimeError());
        response.setSubmittedAt(submission.getSubmittedAt());
        return response;
    }
}


//    @GetMapping("/submissions/user/{userId}")
//    public ResponseEntity<List<SubmissionResponse>> getUserSubmissions(
//            @PathVariable Long userId,
//            @RequestParam(required = false) String problemId) {
//        List<Submission> submissions;
//
//        if (problemId != null && !problemId.isEmpty()) {
//            submissions = codeExecutionService.getUserSubmissions(userId, problemId);
//        } else {
//            submissions = codeExecutionService.getUserSubmissions(userId);
//        }
//
//        List<SubmissionResponse> responses = submissions.stream()
//                .map(this::convertToResponse)
//                .toList();
//
//        return ResponseEntity.ok(responses);
//    }
