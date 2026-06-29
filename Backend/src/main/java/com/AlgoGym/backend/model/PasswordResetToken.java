package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "password_reset_tokens")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PasswordResetToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Which user this token belongs to
    @Column(name = "user_id", nullable = false)
    private String userId;

    // The actual token string (UUID)
    @Column(nullable = false, unique = true)
    private String token;

    // When it stops being valid
    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    // Prevent reuse after password reset
    @Column(nullable = false)
    @Builder.Default
    private boolean used = false;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    // ---- Helper methods ----

    public boolean isExpired() {
        return LocalDateTime.now().isAfter(this.expiresAt);
    }

    public boolean isValid() {
        return !used && !isExpired();
    }
}