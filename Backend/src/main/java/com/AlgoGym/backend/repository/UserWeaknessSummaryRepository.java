package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.UserWeaknessSummary;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserWeaknessSummaryRepository extends JpaRepository<UserWeaknessSummary, Long> {

    Optional<UserWeaknessSummary> findByUserId(String userId);
}
