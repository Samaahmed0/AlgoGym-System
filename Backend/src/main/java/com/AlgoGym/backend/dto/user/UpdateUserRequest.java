package com.AlgoGym.backend.dto.user;

import lombok.Data;

@Data
public class UpdateUserRequest {
    private String username;
    private String email;
    private String currentPassword;
    private String newPassword;
    private String skillLevel;
    private String bio;
    private String githubUrl;
    private String avatarUrl;
}