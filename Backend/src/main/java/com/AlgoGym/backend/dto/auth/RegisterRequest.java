package com.AlgoGym.backend.dto.auth;

import lombok.Data;

@Data
public class RegisterRequest {
    private String username;
    private String email;
    private String password;
    private String skillLevel; // optional: beginner, intermediate, advanced
}