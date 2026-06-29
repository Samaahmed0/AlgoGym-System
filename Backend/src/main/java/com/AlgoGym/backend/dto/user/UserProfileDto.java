package com.AlgoGym.backend.dto.user;

import com.AlgoGym.backend.model.User;
import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class UserProfileDto {

    private String id;
    private String username;
    private String email;
    private String skillLevel;
    private LocalDateTime createdAt;
    private String bio;
    private String githubUrl;
    private String avatarUrl;

    public static UserProfileDto from(User user) {
        return new UserProfileDto(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getSkillLevel(),
                user.getCreatedAt(),
                user.getBio(),
                user.getGithubUrl(),
                user.getAvatarUrl()
        );
    }
}