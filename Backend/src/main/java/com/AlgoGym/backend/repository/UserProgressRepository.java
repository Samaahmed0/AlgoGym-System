package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.UserProgress;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface UserProgressRepository extends JpaRepository<UserProgress, Long> {

    Optional<UserProgress> findByUserId(String userId);

    // Get user's rank
    @Query("""
        SELECT COUNT(up) + 1
        FROM UserProgress up
        WHERE up.problemsSolved > (
            SELECT up2.problemsSolved
            FROM UserProgress up2
            WHERE up2.userId = :userId
        )
    """)
    Long getUserRank(@Param("userId") String userId);

    // Total users
    @Query("SELECT COUNT(up) FROM UserProgress up")
    Long getTotalUsers();

    @Query("SELECT AVG(up.acceptanceRate) FROM UserProgress up")
    Double findAverageAcceptanceRate();

    void deleteByUserId(String userId);

    @Query(value = """
            SELECT up.user_id, u.username, up.problems_solved, up.acceptance_rate,
                   up.current_streak, up.algorithm_rating
            FROM user_progress up
            JOIN users u ON up.user_id = u.id
            ORDER BY up.problems_solved DESC
            LIMIT :limit
            """, nativeQuery = true)
    List<Object[]> findMostActiveUsers(@Param("limit") int limit);
}