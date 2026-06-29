package com.AlgoGym.backend.dto;

import com.AlgoGym.backend.model.TestCase;
import lombok.*;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Setter
@Getter
@Builder
public class ProblemDTO {
    private String id;
    private String title;
    private String description;
    private String difficulty;
    private Long rating;
    private List<String> tags;
    private Double timeLimit;
    private Long memoryLimit;
    private List<TestCase> examples;
    private String inputFormat;
    private String outputFormat;
    private String note;
    private String editorial;
    private String status;      // "solved", "attempted", or "unsolved"
    private Double acceptance;  // Acceptance rate percentage

}