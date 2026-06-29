package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.UserTagStats;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface UserTagStatsRepository extends JpaRepository<UserTagStats, Long> {

    Optional<UserTagStats> findByUserIdAndTag(String userId, String tag);

    // Top N tags by submission count for dashboard
    @Query("""
        SELECT u FROM UserTagStats u
        WHERE u.userId = :userId
        ORDER BY u.submissions DESC
    """)
    List<UserTagStats> findByUserIdOrderBySubmissionsDesc(@Param("userId") String userId);

    // Total submissions across all tags for this user (for percentage calc)
    @Query("""
        SELECT COALESCE(SUM(u.submissions), 0)
        FROM UserTagStats u
        WHERE u.userId = :userId
    """)
    Long getTotalTagSubmissions(@Param("userId") String userId);

    void deleteByUserId(String userId);

    @Query("""
            SELECT uts.tag, SUM(uts.submissions), SUM(uts.solved)
            FROM UserTagStats uts
            GROUP BY uts.tag
            """)
    List<Object[]> findTagSubmissionTotals();

    @Modifying
    @Query("UPDATE UserTagStats uts SET uts.tag = :newTag WHERE uts.tag = :oldTag")
    int renameTag(@Param("oldTag") String oldTag, @Param("newTag") String newTag);
}