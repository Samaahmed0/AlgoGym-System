package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.progress.ProgressResponse;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.service.ProgressService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/progress")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ProgressController {

    private final ProgressService progressService;
    private final UserRepository userRepository;

    @GetMapping("/me")
    public ResponseEntity<ProgressResponse> getMyProgress(Authentication authentication) {
        String username = authentication.getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));

        ProgressResponse response = progressService.getProgress(user.getId());
        return ResponseEntity.ok(response);
    }
}