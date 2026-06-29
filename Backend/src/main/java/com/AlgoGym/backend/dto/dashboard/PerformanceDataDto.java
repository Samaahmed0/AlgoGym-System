package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class PerformanceDataDto {
    private String date;  // "2026-02-01"
    private Integer xp;
    private Integer submissions;
}