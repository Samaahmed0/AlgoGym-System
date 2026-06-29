package com.AlgoGym.backend.dto.recommendations;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RecommendationsResponse {
    private LocalDateTime lastUpdated;
    private int totalPicks;
    private int weakAreasCount;
    private List<WeakAreaRecommendationsDto> weakAreas;
}
