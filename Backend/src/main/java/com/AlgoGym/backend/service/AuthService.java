package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.auth.AuthResponse;
import com.AlgoGym.backend.dto.auth.LoginRequest;
import com.AlgoGym.backend.dto.auth.RegisterRequest;
import com.AlgoGym.backend.model.Role;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.model.UserProgress;
import com.AlgoGym.backend.repository.UserProgressRepository;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.security.JwtUtil;
import com.AlgoGym.backend.util.PasswordValidator;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final AuthenticationManager authenticationManager;
    private final UserProgressService userProgressService;

    public AuthResponse register(RegisterRequest request) {
        // Validate password
        if (!PasswordValidator.isValid(request.getPassword())) {
            throw new IllegalArgumentException(PasswordValidator.getRequirements());
        }

        if (userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists");
        }
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists");
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setRole(Role.USER);
        user.setSkillLevel(request.getSkillLevel() != null ? request.getSkillLevel() : "beginner");


        userRepository.save(user);
        userProgressService.initializeProgress(user.getId());

        String token = jwtUtil.generateToken(user);

        return new AuthResponse(token, user.getUsername(), user.getEmail(), user.getRole().name());
    }

    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getUsername(),
                        request.getPassword()
                )
        );

        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        String token = jwtUtil.generateToken(user);

        return new AuthResponse(token, user.getUsername(), user.getEmail(), user.getRole().name());
    }

    public User getCurrentUser(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));
    }
}