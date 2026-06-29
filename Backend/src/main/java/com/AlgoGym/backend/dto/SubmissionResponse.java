package com.AlgoGym.backend.dto;

import com.AlgoGym.backend.model.TestResult;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;


@Setter
@Getter
public class SubmissionResponse {
    private Long submissionId;
    private String verdict;
    private Integer passedTests;
    private Integer totalTests;
    private Double executionTimeMs;
    private Double memoryUsedKb;
    private List<TestResult> testResults;
    private String firstFailedInput;
    private String firstFailedExpected;
    private String firstFailedActual;
    private String compilationError;
    private String runtimeError;
    private LocalDateTime submittedAt;

    private String aiErrorType;
    private String aiExplanation;
    private List<String> aiTips;
    public SubmissionResponse() {}

}