package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.Recommendation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RecommendationRepository extends JpaRepository<Recommendation, Long> {

    List<Recommendation> findByUserIdOrderByIdAsc(String userId);

    void deleteByUserId(String userId);
}
