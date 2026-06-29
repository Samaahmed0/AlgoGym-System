package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.PasswordResetToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.Optional;

public interface PasswordResetTokenRepository extends JpaRepository<PasswordResetToken, Long> {

    // Find token for validation during reset
    Optional<PasswordResetToken> findByToken(String token);

    // Count recent requests for rate limiting
    // Checks: same user, created within last hour, (used or not - counts all attempts)
    @Query("""
        SELECT COUNT(t) FROM PasswordResetToken t
        WHERE t.userId = :userId
        AND t.createdAt >= :since
    """)
    long countRecentRequests(@Param("userId") String userId,
                             @Param("since") LocalDateTime since);

    // Cleanup old tokens (optional, call in a scheduled job)
    @Query("""
        DELETE FROM PasswordResetToken t
        WHERE t.expiresAt < :now
    """)
    @org.springframework.data.jpa.repository.Modifying
    @jakarta.transaction.Transactional
    void deleteExpiredTokens(@Param("now") LocalDateTime now);
}