package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.user.UpdateUserRequest;
import com.AlgoGym.backend.dto.user.UserProfileDto;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.util.PasswordValidator;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;  // ADD THIS

    public UserProfileDto getUserById(String id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return UserProfileDto.from(user);
    }

    public UserProfileDto updateUser(String id, UpdateUserRequest request, String authenticatedUsername) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // Security: Users can only update their own profile
        if (!user.getUsername().equals(authenticatedUsername)) {
            throw new RuntimeException("Unauthorized: You can only update your own profile");
        }

        // Update username (check uniqueness)
        if (request.getUsername() != null && !request.getUsername().equals(user.getUsername())) {
            if (userRepository.existsByUsername(request.getUsername())) {
                throw new RuntimeException("Username already taken");
            }
            user.setUsername(request.getUsername());
        }

        // Update email (check uniqueness)
        if (request.getEmail() != null && !request.getEmail().equals(user.getEmail())) {
            if (userRepository.existsByEmail(request.getEmail())) {
                throw new RuntimeException("Email already taken");
            }
            user.setEmail(request.getEmail());
        }

        // Update password (verify current password first and validate new password)
        if (request.getNewPassword() != null) {
            if (request.getCurrentPassword() == null) {
                throw new RuntimeException("Current password required to change password");
            }
            if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPassword())) {
                throw new RuntimeException("Current password is incorrect");
            }
            // Validate new password
            if (!PasswordValidator.isValid(request.getNewPassword())) {
                throw new RuntimeException(PasswordValidator.getRequirements());
            }
            user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        }


        if (request.getSkillLevel() != null) {
            user.setSkillLevel(request.getSkillLevel());
        }


        if (request.getBio() != null) {
            user.setBio(request.getBio());
        }


        if (request.getGithubUrl() != null) {
            user.setGithubUrl(request.getGithubUrl());
        }

        if (request.getAvatarUrl() != null) {
            user.setAvatarUrl(request.getAvatarUrl());
        }

        userRepository.save(user);
        return UserProfileDto.from(user);
    }
}