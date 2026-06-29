package com.AlgoGym.backend.exception;

// One file, multiple exception classes - keeps it organized

public class PasswordResetException {

    public static class TokenNotFoundException extends RuntimeException {
        public TokenNotFoundException() {
            super("Invalid or expired password reset token");
            // Intentionally vague - don't tell attackers if a token exists
        }
    }

    public static class TokenExpiredException extends RuntimeException {
        public TokenExpiredException() {
            super("Password reset token has expired. Please request a new one.");
        }
    }

    public static class TokenAlreadyUsedException extends RuntimeException {
        public TokenAlreadyUsedException() {
            super("Password reset token has already been used.");
        }
    }

    public static class RateLimitExceededException extends RuntimeException {
        public RateLimitExceededException() {
            super("Too many password reset requests. Please wait before trying again.");
        }
    }
}