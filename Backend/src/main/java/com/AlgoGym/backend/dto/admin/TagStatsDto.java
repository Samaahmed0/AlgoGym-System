package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TagStatsDto {
    private String tag;
    private Long problemCount;
    private Long totalUserSubmissions;
    private Long totalUserSolved;
}
