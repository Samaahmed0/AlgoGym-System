package com.AlgoGym.backend.dto.progress;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class HeatmapEntryDto {
    private String date;
    private Integer count;
}