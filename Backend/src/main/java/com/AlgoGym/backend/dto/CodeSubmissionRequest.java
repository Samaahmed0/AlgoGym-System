package com.AlgoGym.backend.dto;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CodeSubmissionRequest {
    private String problemId;
    private String sourceCode;
    private Integer languageId;
    private String languageName;
}