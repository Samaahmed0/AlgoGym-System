package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AIFeedbackStatsDto {
    private Long totalFeedbackThisWeek;
    private Long totalFeedbackAllTime;
    private List<ErrorTypeCountDto> errorTypeBreakdown;
    private List<ProblematicProblemDto> problemsNeedingReview;
    private List<RecentFeedbackDto> recentFeedback;
}
