package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.ProblemDTO;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.service.ProblemService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/problems")
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:5173")

public class ProblemController {

    private final ProblemService problemService;
    private final UserRepository userRepository;

    @GetMapping
    public Page<ProblemDTO> getProblems(
            @RequestParam(required = false) List<String> difficulty,
            @RequestParam(required = false) List<String> tags,
            @RequestParam(required = false) List<String> status,
            @RequestParam(required = false) String title,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
            , Authentication authentication
    ) {
        String userId = null;
        // If the request is authenticated, enrich results with per-user status/acceptance.
        // (Completion-status filtering also relies on userId.)
        if (authentication != null) {
            String username = authentication.getName();
            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new RuntimeException("User not found"));
            userId = user.getId();
        }
        return problemService.getProblemsByFilters(difficulty, tags, title, status, userId, page, size);
    }

    @GetMapping("/tags")
    public List<String> getProblemTags() {
        return problemService.getAllTags();
    }

    @GetMapping("/{id}")
    public ProblemDTO getProblemById(@PathVariable String id) {
        return problemService.getProblemById(id);
    }
}