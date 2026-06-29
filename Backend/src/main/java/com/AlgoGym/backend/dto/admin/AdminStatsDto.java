package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AdminStatsDto {
    private Long totalUsers;
    private Long totalProblems;
    private Long totalSubmissions;
    private Long submissionsToday;
    private Long activeUsersThisWeek;
    private Double overallAcceptanceRate;
    private List<DailyCountDto> dailySubmissions;
    private List<DailyCountDto> dailyRegistrations;
}
