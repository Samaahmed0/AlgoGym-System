package com.AlgoGym.backend.dto.recommendations;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class WeakAreaRecommendationsDto {
    private String id;
    private String name;
    private Integer accuracy;
    private String accent;
    private String insight;
    private List<RecommendationItemDto> recommendations;
}
