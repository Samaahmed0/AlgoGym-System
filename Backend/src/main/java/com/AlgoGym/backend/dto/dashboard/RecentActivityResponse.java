package com.AlgoGym.backend.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class RecentActivityResponse {
    private List<ActivityDto> activities;
    private Integer totalPages;
    private Integer currentPage;
    private Long totalElements;
}