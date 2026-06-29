package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.dashboard.DashboardResponse;
import com.AlgoGym.backend.dto.dashboard.SubmissionSourceDto;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.service.DashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final DashboardService dashboardService;
    private final UserRepository userRepository;

    @GetMapping("/{userId}")
    public ResponseEntity<DashboardResponse> getDashboard(
            @PathVariable String userId,
            @RequestParam(defaultValue = "0") int activityPage,
            @RequestParam(defaultValue = "50") int activitySize
    ) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        DashboardResponse dashboard = dashboardService.getDashboard(
                userId, user.getUsername(), activityPage, activitySize
        );
        return ResponseEntity.ok(dashboard);
    }

    @GetMapping("/me")
    public ResponseEntity<DashboardResponse> getMyDashboard(
            @RequestParam(defaultValue = "0") int activityPage,
            @RequestParam(defaultValue = "6") int activitySize,
            Authentication authentication
    ) {
        String username = authentication.getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));

        DashboardResponse dashboard = dashboardService.getDashboard(
                user.getId(), username, activityPage, activitySize
        );
        return ResponseEntity.ok(dashboard);
    }

    @GetMapping("/me/submissions/{submissionId}/source")
    public ResponseEntity<SubmissionSourceDto> getSubmissionSource(
            @PathVariable Long submissionId,
            Authentication authentication
    ) {
        String username = authentication.getName();
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));

        SubmissionSourceDto source = dashboardService.getSubmissionSource(user.getId(), submissionId);
        return ResponseEntity.ok(source);
    }
}