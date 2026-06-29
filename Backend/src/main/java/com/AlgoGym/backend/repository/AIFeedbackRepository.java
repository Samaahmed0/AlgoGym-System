package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.AIFeedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface AIFeedbackRepository extends JpaRepository<AIFeedback, Long> {
    Optional<AIFeedback> findBySubmissionId(Long submissionId);

    List<AIFeedback> findBySubmissionIdIn(List<Long> submissionIds);

    @Modifying
    @Query("""
            DELETE FROM AIFeedback af
            WHERE af.submissionId IN (
                SELECT s.id FROM Submission s WHERE s.userId = :userId
            )
            """)
    void deleteByUserId(@Param("userId") String userId);

    @Modifying
    @Query("""
            DELETE FROM AIFeedback af
            WHERE af.submissionId IN (
                SELECT s.id FROM Submission s WHERE s.problemId = :problemId
            )
            """)
    void deleteByProblemId(@Param("problemId") String problemId);

    @Query("SELECT COUNT(af) FROM AIFeedback af WHERE af.createdAt >= :since")
    Long countByCreatedAtAfter(@Param("since") LocalDateTime since);

    @Query("""
            SELECT af.errorType, COUNT(af)
            FROM AIFeedback af
            GROUP BY af.errorType
            ORDER BY COUNT(af) DESC
            """)
    List<Object[]> findErrorTypeBreakdown();

    @Query(value = """
            SELECT af.id, s.id as submission_id,
                   u.username, s.problem_id,
                   af.error_type, af.explanation, af.created_at
            FROM ai_feedback af
            JOIN submissions s ON af.submission_id = s.id
            JOIN users u ON s.user_id = u.id
            ORDER BY af.created_at DESC
            LIMIT 20
            """, nativeQuery = true)
    List<Object[]> findRecentFeedbackWithDetails();

    @Query(value = """
            SELECT s.problem_id, p.title,
                   COUNT(af.id) as help_requests,
                   COUNT(DISTINCT s.id) as total_submissions
            FROM ai_feedback af
            JOIN submissions s ON af.submission_id = s.id
            JOIN "Problems" p ON s.problem_id = p.id
            GROUP BY s.problem_id, p.title
            ORDER BY help_requests DESC
            LIMIT 10
            """, nativeQuery = true)
    List<Object[]> findMostProblematicProblems();
}