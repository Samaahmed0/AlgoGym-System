package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AdminAnalyticsOverviewDto {
    private List<DailyCountDto> dailySubmissions;
    private List<DailyCountDto> dailyRegistrations;
    private List<LanguageStatsDto> submissionsByLanguage;
    private List<SkillLevelCountDto> usersBySkillLevel;
}
