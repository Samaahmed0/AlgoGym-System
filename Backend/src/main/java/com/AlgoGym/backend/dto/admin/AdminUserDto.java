package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AdminUserDto {
    private String id;
    private String username;
    private String email;
    private String role;
    private String skillLevel;
    private LocalDateTime createdAt;
    private Integer totalSubmissions;
    private Integer problemsSolved;
    private Integer currentStreak;
    private Double acceptanceRate;
    private Integer algorithmRating;
}
