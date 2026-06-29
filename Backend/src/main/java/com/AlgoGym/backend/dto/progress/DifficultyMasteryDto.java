package com.AlgoGym.backend.dto.progress;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class DifficultyMasteryDto {
    private Integer easySolved;
    private Integer mediumSolved;
    private Integer hardSolved;
    private Long totalEasy;
    private Long totalMedium;
    private Long totalHard;
}