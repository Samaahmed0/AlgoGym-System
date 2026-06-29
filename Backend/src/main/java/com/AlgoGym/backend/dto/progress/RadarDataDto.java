package com.AlgoGym.backend.dto.progress;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class RadarDataDto {
    private List<RadarPointDto> points;
}