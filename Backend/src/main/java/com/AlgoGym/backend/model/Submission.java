package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "submissions")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Submission {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "problem_id", nullable = false)
    private String problemId;

    // The user's code (for ai)
    @Column(name = "source_code", nullable = false, columnDefinition = "TEXT")
    private String sourceCode;

    //every language has an id in the compiler
    @Column(name = "language_id", nullable = false)
    private Integer languageId;

    @Column(name = "language_name")
    private String languageName;

    // ACCEPTED, WRONG_ANSWER, COMPILATION_ERROR, ...
    @Column(name = "verdict", nullable = false)
    private String verdict;

    @Column(name = "passed_tests")
    private Integer passedTests;

    @Column(name = "total_tests")
    private Integer totalTests;

    // Performance metrics
    @Column(name = "execution_time_ms")
    private Double executionTimeMs;

    @Column(name = "memory_used_kb")
    private Double memoryUsedKb;

    @Builder.Default
    // Did it exceed limits?
    @Column(name = "time_limit_exceeded")
    private Boolean timeLimitExceeded = false;
    @Builder.Default
    @Column(name = "memory_limit_exceeded")
    private Boolean memoryLimitExceeded = false;

    // Errors (for AI to analyze)
    @Column(name = "compilation_error", columnDefinition = "TEXT")
    private String compilationError;

    @Column(name = "runtime_error", columnDefinition = "TEXT")
    private String runtimeError;

    // Detailed test results (JSON array)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "test_results", columnDefinition = "jsonb")
    private List<TestResult> testResults;

    // First failed test case (for ui)
    @Column(name = "first_failed_input", columnDefinition = "TEXT")
    private String firstFailedInput;

    @Column(name = "first_failed_expected", columnDefinition = "TEXT")
    private String firstFailedExpected;

    @Column(name = "first_failed_actual", columnDefinition = "TEXT")
    private String firstFailedActual;

    @CreationTimestamp
    @Column(name = "submitted_at", updatable = false)
    private LocalDateTime submittedAt;


}