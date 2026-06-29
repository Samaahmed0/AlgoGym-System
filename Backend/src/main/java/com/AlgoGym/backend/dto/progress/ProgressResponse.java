package com.AlgoGym.backend.dto.progress;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class ProgressResponse {
    private List<HeatmapEntryDto> heatmap;
    private RadarDataDto radarData;
    private DifficultyMasteryDto difficultyMastery;
    private String aiInsight;
}