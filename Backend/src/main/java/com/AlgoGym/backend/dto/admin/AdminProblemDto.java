package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class AdminProblemDto {
    private String id;
    private String title;
    private Long rating;
    private List<String> tags;
    private Double timeLimit;
    private Long memoryLimit;
    private Boolean isVisible;
    private Long totalSubmissions;
    private Double acceptanceRate;
}
