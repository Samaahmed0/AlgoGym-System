package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SubmissionSourceDto {
    private String sourceCode;
    private String language;
    private String problemTitle;
}
