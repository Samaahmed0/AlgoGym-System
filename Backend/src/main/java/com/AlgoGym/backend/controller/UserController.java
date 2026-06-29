package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.user.UpdateUserRequest;
import com.AlgoGym.backend.dto.user.UserProfileDto;
import com.AlgoGym.backend.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserProfileDto> getUser(@PathVariable String id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateUser(
            @PathVariable String id,
            @RequestBody UpdateUserRequest request,
            Authentication authentication
    ) {
        try {
            String authenticatedUsername = authentication.getName();
            return ResponseEntity.ok(userService.updateUser(id, request, authenticatedUsername));
        } catch (RuntimeException ex) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", ex.getMessage() != null ? ex.getMessage() : "Update failed"));
        }
    }
}