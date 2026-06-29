package com.AlgoGym.backend.dto.recommendations;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RecommendationItemDto {
    private String problemId;
    private String title;
    private String difficulty;
    private String topic;
    private String reason;
    private Double confidenceScore;
}
