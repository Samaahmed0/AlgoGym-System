package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserStatsDto {
    private String username;
    private Integer totalSolved;
    private Integer easySolved;
    private Integer mediumSolved;
    private Integer hardSolved;
    private Integer currentStreak;
    private Double acceptanceRate;
    private String globalRank;  // "TOP 5%" or "#1284"
    private Integer algorithmRating;  // Placeholder for now
    private Integer newlySolvedToday;   // for "+4 NEW"
    private String velocityMessage;      // "Your analytical velocity increased by X% this week"
}