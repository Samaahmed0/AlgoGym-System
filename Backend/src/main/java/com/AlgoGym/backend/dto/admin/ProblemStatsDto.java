package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ProblemStatsDto {
    private String problemId;
    private String title;
    private Long totalSubmissions;
    private Long accepted;
    private Double acceptanceRate;
    private String difficulty;
}
