package com.AlgoGym.backend.service;

import com.AlgoGym.backend.exception.PasswordResetException;
import com.AlgoGym.backend.model.PasswordResetToken;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.PasswordResetTokenRepository;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.util.PasswordValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class PasswordResetService {

    private final UserRepository userRepository;
    private final PasswordResetTokenRepository tokenRepository;
    private final EmailService emailService;
    private final PasswordEncoder passwordEncoder;
    private final PasswordValidator passwordValidator;

    @Value("${app.password-reset.expiry-minutes:60}")
    private int expiryMinutes;

    @Value("${app.password-reset.max-requests-per-hour:3}")
    private int maxRequestsPerHour;

    /**
     * STEP 1 of reset flow: User submits email.
     *
     * Security note: We ALWAYS return success even if email doesn't exist.
     * This prevents "email enumeration attacks" where an attacker probes
     * which emails are registered by watching for different responses.
     */
    @Transactional
    public void initiatePasswordReset(String email) {
        Optional<User> userOpt = userRepository.findByEmail(email);

        // Always log but silently succeed if email not found
        if (userOpt.isEmpty()) {
            log.info("Password reset requested for non-existent email: {}", email);
            return; // Return success to frontend - don't reveal email doesn't exist
        }

        User user = userOpt.get();

        // Rate limiting check
        LocalDateTime oneHourAgo = LocalDateTime.now().minusHours(1);
        long recentRequests = tokenRepository.countRecentRequests(user.getId(), oneHourAgo);

        if (recentRequests >= maxRequestsPerHour) {
            log.warn("Rate limit exceeded for user: {}", user.getId());
            throw new PasswordResetException.RateLimitExceededException();
        }

        // Generate secure token
        String token = UUID.randomUUID().toString();
        LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(expiryMinutes);

        // Save token to database
        PasswordResetToken resetToken = PasswordResetToken.builder()
                .userId(user.getId())
                .token(token)
                .expiresAt(expiresAt)
                .build();

        tokenRepository.save(resetToken);

        // Send email (if this throws, transaction rolls back the token save - good!)
        emailService.sendPasswordResetEmail(user.getEmail(), token);

        log.info("Password reset initiated for user: {}", user.getId());
    }

    /**
     * STEP 2 of reset flow: User submits new password with token.
     */
    @Transactional
    public void resetPassword(String token, String newPassword) {
        // Find the token
        PasswordResetToken resetToken = tokenRepository.findByToken(token)
                .orElseThrow(PasswordResetException.TokenNotFoundException::new);

        // Validate state (order matters - check used before expired for better UX)
        if (resetToken.isUsed()) {
            throw new PasswordResetException.TokenAlreadyUsedException();
        }

        if (resetToken.isExpired()) {
            throw new PasswordResetException.TokenExpiredException();
        }

        // Validate new password meets requirements
        if (!passwordValidator.isValid(newPassword)) {
            throw new IllegalArgumentException(
                    "Password must be at least 8 characters and contain uppercase, lowercase, number, and special character"
            );
        }

        // Find user and update password
        User user = userRepository.findById(resetToken.getUserId())
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);

        // Mark token as used (prevents reuse)
        resetToken.setUsed(true);
        tokenRepository.save(resetToken);

        log.info("Password successfully reset for user: {}", user.getId());
    }
}