package com.AlgoGym.backend.dto.progress;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class RadarPointDto {
    private String tag;
    private Double acceptanceRate;
    private Integer solved;
    private Integer submissions;
}