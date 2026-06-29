package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class FocusAreaDto {
    private String tag;
    private Integer submissions;
    private Double percentage;  // submissions / total tag submissions * 100
    private Integer solved;
}