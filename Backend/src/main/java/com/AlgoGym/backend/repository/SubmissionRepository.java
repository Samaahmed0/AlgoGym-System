package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.Submission;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;


public interface SubmissionRepository extends JpaRepository<Submission, Long> {

    Page<Submission> findByUserIdOrderBySubmittedAtDesc(String userId, Pageable pageable);

    @Query("""
        SELECT s FROM Submission s
        WHERE s.userId = :userId
        AND s.submittedAt >= :startDate
        ORDER BY s.submittedAt ASC
    """)
    List<Submission> findRecentSubmissions(
            @Param("userId") String userId,
            @Param("startDate") LocalDateTime startDate
    );

    Long countByUserId(String userId);

    @Query("""
    SELECT COUNT(DISTINCT s1.problemId)
    FROM Submission s1
    WHERE s1.userId = :userId
      AND s1.verdict = 'ACCEPTED'
      AND s1.submittedAt >= :since
      AND s1.submittedAt = (
          SELECT MIN(s2.submittedAt)
          FROM Submission s2
          WHERE s2.userId = :userId
            AND s2.problemId = s1.problemId
            AND s2.verdict = 'ACCEPTED'
      )
""")
    Long countNewlySolvedSince(@Param("userId") String userId, @Param("since") LocalDateTime since);

    @Query("""
    SELECT s FROM Submission s
    WHERE s.userId = :userId
    AND s.verdict = 'ACCEPTED'
    AND s.submittedAt >= :startDate
    AND s.submittedAt < :endDate
    ORDER BY s.submittedAt ASC
""")
    List<Submission> findAcceptedBetween(
            @Param("userId") String userId,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate
    );

    @Query("SELECT COUNT(s) FROM Submission s WHERE s.userId = :userId AND s.problemId = :problemId AND s.verdict = 'ACCEPTED'")
    Long countAcceptedSubmissions(@Param("userId") String userId, @Param("problemId") String problemId);

    @Query("""
        SELECT MAX(s.submittedAt)
        FROM Submission s
        WHERE s.userId = :userId
          AND s.verdict = 'ACCEPTED'
          AND s.submittedAt < :before
    """)
    LocalDateTime findPreviousAcceptedAt(
            @Param("userId") String userId,
            @Param("before") LocalDateTime before
    );

    @Query(value = """
    SELECT CAST(DATE(s.submitted_at) AS TEXT) as day, COUNT(*) as count
    FROM submissions s
    WHERE s.user_id = :userId
    AND s.submitted_at >= :startDate
    GROUP BY DATE(s.submitted_at)
    ORDER BY DATE(s.submitted_at)
    """, nativeQuery = true)
    List<Object[]> findDailySubmissionCounts(
            @Param("userId") String userId,
            @Param("startDate") LocalDateTime startDate
    );

    @Query(value = """
            SELECT DATE(submitted_at) as date, COUNT(*) as count
            FROM submissions
            WHERE submitted_at >= :since
            GROUP BY DATE(submitted_at)
            ORDER BY date ASC
            """, nativeQuery = true)
    List<Object[]> findGlobalDailySubmissionCounts(@Param("since") LocalDateTime since);

    @Query(value = """
            SELECT language_name, COUNT(*) as submissions
            FROM submissions
            GROUP BY language_name
            ORDER BY submissions DESC
            """, nativeQuery = true)
    List<Object[]> findSubmissionsByLanguage();

    @Query(value = """
            SELECT s.problem_id, p.title, p.rating,
                   COUNT(*) as total_submissions,
                   SUM(CASE WHEN s.verdict = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted
            FROM submissions s
            JOIN "Problems" p ON s.problem_id = p.id
            GROUP BY s.problem_id, p.title, p.rating
            HAVING COUNT(*) >= :minSubmissions
            ORDER BY (SUM(CASE WHEN s.verdict = 'ACCEPTED' THEN 1 ELSE 0 END)::double precision / COUNT(*)) ASC
            LIMIT :limit
            """, nativeQuery = true)
    List<Object[]> findHardestProblemsByAcceptanceRate(
            @Param("minSubmissions") long minSubmissions,
            @Param("limit") int limit
    );

    @Query(value = """
            SELECT s.problem_id, p.title, p.rating,
                   COUNT(*) as total_submissions,
                   SUM(CASE WHEN s.verdict = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted
            FROM submissions s
            JOIN "Problems" p ON s.problem_id = p.id
            GROUP BY s.problem_id, p.title, p.rating
            HAVING COUNT(*) >= :minSubmissions
            ORDER BY (SUM(CASE WHEN s.verdict = 'ACCEPTED' THEN 1 ELSE 0 END)::double precision / COUNT(*)) DESC
            LIMIT :limit
            """, nativeQuery = true)
    List<Object[]> findEasiestProblemsByAcceptanceRate(
            @Param("minSubmissions") long minSubmissions,
            @Param("limit") int limit
    );

    // ← new method added here
    List<Submission> findByUserIdAndProblemIdIn(String userId, List<String> problemIds);

    @Query("SELECT COUNT(s) FROM Submission s WHERE s.submittedAt >= :since")
    Long countBySubmittedAtAfter(@Param("since") LocalDateTime since);

    @Query("SELECT COUNT(DISTINCT s.userId) FROM Submission s WHERE s.submittedAt >= :since")
    Long countDistinctUserIdBySubmittedAtAfter(@Param("since") LocalDateTime since);

    void deleteByUserId(String userId);

    @Query("SELECT COUNT(s) FROM Submission s WHERE s.problemId = :problemId")
    Long countByProblemId(@Param("problemId") String problemId);

    @Query("""
            SELECT COUNT(s) FROM Submission s
            WHERE s.problemId = :problemId
            AND s.verdict = 'ACCEPTED'
            """)
    Long countAcceptedByProblemId(@Param("problemId") String problemId);

    @Query("""
            SELECT s.problemId, COUNT(s),
                   SUM(CASE WHEN s.verdict = 'ACCEPTED' THEN 1L ELSE 0L END)
            FROM Submission s
            WHERE s.problemId IN :problemIds
            GROUP BY s.problemId
            """)
    List<Object[]> countSubmissionStatsByProblemIds(@Param("problemIds") List<String> problemIds);

    void deleteByProblemId(String problemId);

    @Query(value = """
            SELECT s.id, s.user_id, s.problem_id, s.language_name, s.verdict,
                   s.passed_tests, s.total_tests, s.execution_time_ms, s.memory_used_kb,
                   s.submitted_at, u.username, p.title AS problem_title
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN "Problems" p ON s.problem_id = p.id
            WHERE (:verdict IS NULL OR s.verdict = :verdict)
              AND (:language IS NULL OR s.language_name = :language)
              AND (:userId IS NULL OR s.user_id = :userId)
              AND (:problemId IS NULL OR s.problem_id = :problemId)
            ORDER BY s.submitted_at DESC
            """,
            countQuery = """
            SELECT COUNT(*)
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN "Problems" p ON s.problem_id = p.id
            WHERE (:verdict IS NULL OR s.verdict = :verdict)
              AND (:language IS NULL OR s.language_name = :language)
              AND (:userId IS NULL OR s.user_id = :userId)
              AND (:problemId IS NULL OR s.problem_id = :problemId)
            """,
            nativeQuery = true)
    Page<Object[]> findAdminSubmissions(
            @Param("verdict") String verdict,
            @Param("language") String language,
            @Param("userId") String userId,
            @Param("problemId") String problemId,
            Pageable pageable
    );
}