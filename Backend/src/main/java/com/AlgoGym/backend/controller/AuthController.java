package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.auth.AuthResponse;
import com.AlgoGym.backend.dto.auth.LoginRequest;
import com.AlgoGym.backend.dto.auth.RegisterRequest;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.service.AuthService;
import com.AlgoGym.backend.dto.auth.ForgotPasswordRequest;
import com.AlgoGym.backend.dto.auth.ResetPasswordRequest;
import com.AlgoGym.backend.service.PasswordResetService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;


@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {


    private final AuthService authService;
    private final PasswordResetService passwordResetService;

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@RequestBody RegisterRequest request) {
        return ResponseEntity.ok(authService.register(request));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @GetMapping("/me")
    public ResponseEntity<User> getCurrentUser(Authentication authentication) {
        String username = authentication.getName();
        return ResponseEntity.ok(authService.getCurrentUser(username));
    }

    @PostMapping("/logout")
    public ResponseEntity<String> logout() {
        return ResponseEntity.ok("Logged out successfully");
    }


    @PostMapping("/forgot-password")
    public ResponseEntity<Map<String, String>> forgotPassword(
            @Valid @RequestBody ForgotPasswordRequest request) {

        passwordResetService.initiatePasswordReset(request.getEmail());

        // Always return 200 with the same message (prevents email enumeration)
        return ResponseEntity.ok(Map.of(
                "message", "If that email is registered, you'll receive a reset link shortly."
        ));
    }

    @PostMapping("/reset-password")
    public ResponseEntity<Map<String, String>> resetPassword(
            @Valid @RequestBody ResetPasswordRequest request) {

        passwordResetService.resetPassword(request.getToken(), request.getNewPassword());

        return ResponseEntity.ok(Map.of(
                "message", "Password successfully reset. You can now log in."
        ));
    }



}