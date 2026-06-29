package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class RoleChangeLogDto {
    private String targetUserId;
    private String targetUsername;
    private String oldRole;
    private String newRole;
    private String changedByAdminId;
    private String changedByAdminUsername;
    private LocalDateTime changedAt;
}
