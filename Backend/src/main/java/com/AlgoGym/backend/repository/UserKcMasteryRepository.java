package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.UserKcMastery;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserKcMasteryRepository extends JpaRepository<UserKcMastery, Long> {

    List<UserKcMastery> findByUserId(String userId);

    Optional<UserKcMastery> findByUserIdAndKcNameIgnoreCase(String userId, String kcName);
}
