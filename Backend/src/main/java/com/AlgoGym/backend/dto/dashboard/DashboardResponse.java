package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class DashboardResponse {
    private UserStatsDto stats;
    private List<PerformanceDataDto> performanceData;
    private RecentActivityResponse recentActivity;
    private List<FocusAreaDto> focusAreas;
}