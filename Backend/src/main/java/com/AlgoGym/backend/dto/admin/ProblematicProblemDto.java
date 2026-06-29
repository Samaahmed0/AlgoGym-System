package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ProblematicProblemDto {
    private String problemId;
    private String problemTitle;
    private Long helpRequests;
    private Long totalSubmissions;
    private Double helpRequestRate;
}
