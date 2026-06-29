package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "role_change_log")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RoleChangeLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_user_id", nullable = false)
    private String targetUserId;

    @Column(name = "target_username", nullable = false)
    private String targetUsername;

    @Column(name = "old_role", nullable = false)
    private String oldRole;

    @Column(name = "new_role", nullable = false)
    private String newRole;

    @Column(name = "changed_by_admin_id", nullable = false)
    private String changedByAdminId;

    @Column(name = "changed_by_admin_username", nullable = false)
    private String changedByAdminUsername;

    @Column(name = "changed_at", nullable = false)
    private LocalDateTime changedAt;
}
