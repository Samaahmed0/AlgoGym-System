package com.AlgoGym.backend.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TestResult {
    private Integer testNumber;
    private Boolean passed;
    private String input;
    private String expectedOutput;
    private String actualOutput;
    private String error;
    private Double executionTime;
    private Double memoryUsed;
}