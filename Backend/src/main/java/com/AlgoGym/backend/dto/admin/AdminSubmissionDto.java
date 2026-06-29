package com.AlgoGym.backend.dto.admin;

import com.AlgoGym.backend.model.TestResult;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AdminSubmissionDto {
    private Long id;
    private String userId;
    private String username;
    private String problemId;
    private String problemTitle;
    private String languageName;
    private String verdict;
    private Integer passedTests;
    private Integer totalTests;
    private Double executionTimeMs;
    private Double memoryUsedKb;
    private LocalDateTime submittedAt;
    private String sourceCode;
    private String aiErrorType;
    private String aiExplanation;
    private List<TestResult> testResults;
}
