package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SystemHealthDto {
    private String databaseStatus;
    private Long databaseLatencyMs;
    private String judge0Status;
    private Long judge0LatencyMs;
    private String groqStatus;
    private Long groqLatencyMs;
    private LocalDateTime checkedAt;
}
