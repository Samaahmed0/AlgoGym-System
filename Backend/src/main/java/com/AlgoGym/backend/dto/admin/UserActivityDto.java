package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserActivityDto {
    private String userId;
    private String username;
    private Integer problemsSolved;
    private Double acceptanceRate;
    private Integer currentStreak;
    private Integer algorithmRating;
}
