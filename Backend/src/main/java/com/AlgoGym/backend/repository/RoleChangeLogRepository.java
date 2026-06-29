package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.RoleChangeLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RoleChangeLogRepository extends JpaRepository<RoleChangeLog, Long> {

    List<RoleChangeLog> findTop20ByOrderByChangedAtDesc();

    void deleteByTargetUserId(String targetUserId);

    void deleteByChangedByAdminId(String changedByAdminId);
}
