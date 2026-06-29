package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class RecentFeedbackDto {
    private Long feedbackId;
    private Long submissionId;
    private String username;
    private String problemId;
    private String errorType;
    private String explanation;
    private LocalDateTime createdAt;
}
