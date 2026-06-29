package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivityDto {
    private String problemId;
    private Long submissionId;
    private String problemTitle;
    private String difficulty;  // EASY, MEDIUM, HARD
    private String verdict;  // ACCEPTED, WRONG_ANSWER, etc.
    private LocalDateTime submittedAt;
    private String tag;  // Main topic tag
    private String runtime;
    private String memory;
    private String language;
    private Integer testsPassed;
    private Integer totalTests;
}
