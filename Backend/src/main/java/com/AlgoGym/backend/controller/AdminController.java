package com.AlgoGym.backend.controller;

import com.AlgoGym.backend.dto.admin.SystemSettingsDto;
import com.AlgoGym.backend.dto.admin.AdminAnalyticsOverviewDto;
import com.AlgoGym.backend.dto.admin.AdminSubmissionDto;
import com.AlgoGym.backend.dto.admin.AdminProblemDto;
import com.AlgoGym.backend.dto.admin.AdminStatsDto;
import com.AlgoGym.backend.dto.admin.AdminUserDto;
import com.AlgoGym.backend.dto.admin.BulkImportResultDto;
import com.AlgoGym.backend.dto.admin.ProblemStatsDto;
import com.AlgoGym.backend.dto.admin.UserActivityDto;
import com.AlgoGym.backend.dto.admin.RoleChangeLogDto;
import com.AlgoGym.backend.model.Role;
import com.AlgoGym.backend.model.RoleChangeLog;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.model.UserProgress;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.RoleChangeLogRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.UserProgressRepository;
import com.AlgoGym.backend.repository.UserRepository;
import com.AlgoGym.backend.repository.UserTagStatsRepository;
import com.AlgoGym.backend.dto.admin.AIFeedbackStatsDto;
import com.AlgoGym.backend.dto.admin.TagStatsDto;
import com.AlgoGym.backend.dto.admin.SystemHealthDto;
import com.AlgoGym.backend.service.AdminAIFeedbackService;
import com.AlgoGym.backend.service.AdminAnalyticsService;
import com.AlgoGym.backend.service.AdminProblemService;
import com.AlgoGym.backend.service.AdminSubmissionService;
import com.AlgoGym.backend.service.AdminTagService;
import com.AlgoGym.backend.dto.notification.CreateNotificationRequest;
import com.AlgoGym.backend.dto.notification.NotificationDto;
import com.AlgoGym.backend.service.AdminSettingsService;
import com.AlgoGym.backend.service.HealthCheckService;
import com.AlgoGym.backend.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/admin")
@PreAuthorize("hasRole('ADMIN')")
@RequiredArgsConstructor
public class AdminController {

    private static final Logger log = LoggerFactory.getLogger(AdminController.class);

    private final UserRepository userRepository;
    private final ProblemRepository problemRepository;
    private final SubmissionRepository submissionRepository;
    private final UserProgressRepository userProgressRepository;
    private final UserTagStatsRepository userTagStatsRepository;
    private final AIFeedbackRepository aiFeedbackRepository;
    private final RoleChangeLogRepository roleChangeLogRepository;
    private final HealthCheckService healthCheckService;
    private final AdminProblemService adminProblemService;
    private final AdminSubmissionService adminSubmissionService;
    private final AdminAnalyticsService adminAnalyticsService;
    private final AdminTagService adminTagService;
    private final AdminAIFeedbackService adminAIFeedbackService;
    private final NotificationService notificationService;
    private final AdminSettingsService adminSettingsService;

    @GetMapping("/stats")
    public AdminStatsDto getStats() {
        LocalDateTime startOfToday = LocalDate.now().atStartOfDay();
        LocalDateTime weekAgo = LocalDateTime.now().minusDays(7);

        Long totalUsers = userRepository.count();
        Long totalProblems = problemRepository.count();
        Long totalSubmissions = submissionRepository.count();
        Long submissionsToday = submissionRepository.countBySubmittedAtAfter(startOfToday);
        Long activeUsersThisWeek = submissionRepository.countDistinctUserIdBySubmittedAtAfter(weekAgo);
        Double overallAcceptanceRate = userProgressRepository.findAverageAcceptanceRate();

        AdminAnalyticsOverviewDto trends = adminAnalyticsService.getOverview(30);

        return new AdminStatsDto(
                totalUsers,
                totalProblems,
                totalSubmissions,
                submissionsToday,
                activeUsersThisWeek,
                overallAcceptanceRate,
                trends.getDailySubmissions(),
                trends.getDailyRegistrations()
        );
    }

    @GetMapping("/health")
    public SystemHealthDto getHealth() {
        try {
            HealthCheckService.HealthCheckResult database = healthCheckService.checkDatabase();
            HealthCheckService.HealthCheckResult judge0 = healthCheckService.checkJudge0();
            HealthCheckService.HealthCheckResult groq = healthCheckService.checkGroq();

            return new SystemHealthDto(
                    database.getStatus(),
                    database.getLatencyMs(),
                    judge0.getStatus(),
                    judge0.getLatencyMs(),
                    groq.getStatus(),
                    groq.getLatencyMs(),
                    LocalDateTime.now()
            );
        } catch (Exception e) {
            return new SystemHealthDto(
                    "OFFLINE",
                    -1L,
                    "OFFLINE",
                    -1L,
                    "OFFLINE",
                    -1L,
                    LocalDateTime.now()
            );
        }
    }

    @GetMapping("/users")
    public Page<AdminUserDto> getUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "") String search
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<User> usersPage;

        if (search != null && !search.isBlank()) {
            usersPage = userRepository.findByUsernameContainingIgnoreCaseOrEmailContainingIgnoreCase(
                    search, search, pageable);
        } else {
            usersPage = userRepository.findAll(pageable);
        }

        return usersPage.map(this::toAdminUserDto);
    }

    @GetMapping("/users/role-change-log")
    public List<RoleChangeLogDto> getRoleChangeLog() {
        return roleChangeLogRepository.findTop20ByOrderByChangedAtDesc().stream()
                .map(this::toRoleChangeLogDto)
                .toList();
    }

    @DeleteMapping("/users/{userId}")
    @Transactional
    public ResponseEntity<Map<String, String>> deleteUser(
            @PathVariable String userId,
            Authentication authentication
    ) {
        String adminId = getUserIdFromAuth(authentication);
        if (adminId.equals(userId)) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Admins cannot delete their own account"));
        }

        userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        aiFeedbackRepository.deleteByUserId(userId);
        submissionRepository.deleteByUserId(userId);
        userProgressRepository.deleteByUserId(userId);
        userTagStatsRepository.deleteByUserId(userId);
        roleChangeLogRepository.deleteByTargetUserId(userId);
        roleChangeLogRepository.deleteByChangedByAdminId(userId);
        userRepository.deleteById(userId);

        return ResponseEntity.ok(Map.of("message", "User deleted successfully"));
    }

    @PutMapping("/users/{userId}/role")
    public ResponseEntity<?> updateUserRole(
            @PathVariable String userId,
            @RequestBody Map<String, String> body,
            Authentication authentication
    ) {
        String adminId = getUserIdFromAuth(authentication);
        if (adminId.equals(userId)) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Admins cannot change their own role"));
        }

        String roleValue = body.get("role");
        if (roleValue == null || roleValue.isBlank()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Role is required"));
        }

        Role newRole;
        try {
            newRole = Role.valueOf(roleValue.toUpperCase());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Invalid role. Must be ADMIN or USER"));
        }

        User targetUser = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        User admin = userRepository.findById(adminId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Admin not found"));

        String oldRole = targetUser.getRole().name();
        targetUser.setRole(newRole);
        userRepository.save(targetUser);

        RoleChangeLog logEntry = new RoleChangeLog(
                null,
                targetUser.getId(),
                targetUser.getUsername(),
                oldRole,
                newRole.name(),
                admin.getId(),
                admin.getUsername(),
                LocalDateTime.now()
        );
        roleChangeLogRepository.save(logEntry);

        return ResponseEntity.ok(toAdminUserDto(targetUser));
    }

    @GetMapping("/problems")
    public Page<AdminProblemDto> getProblems(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "") String search,
            @RequestParam(defaultValue = "") String difficulty,
            @RequestParam(defaultValue = "all") String visible
    ) {
        return adminProblemService.getAdminProblems(page, size, search, difficulty, visible);
    }

    // Use ?id=1108/A query param — problem IDs may contain slashes (Tomcat rejects %2F in paths).
    @PutMapping("/problems/visibility")
    public AdminProblemDto updateProblemVisibility(
            @RequestParam String id,
            @RequestBody Map<String, Boolean> body
    ) {
        Boolean visible = body.get("visible");
        if (visible == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "visible field is required");
        }
        return adminProblemService.updateVisibility(id, visible);
    }

    @DeleteMapping("/problems")
    @Transactional
    public ResponseEntity<Map<String, String>> deleteProblem(@RequestParam String id) {
        adminProblemService.deleteProblem(id);
        return ResponseEntity.ok(Map.of("message", "Problem deleted successfully"));
    }

    @PostMapping("/problems/bulk-import")
    public BulkImportResultDto bulkImportProblems(
            @RequestParam("file") MultipartFile file,
            @RequestParam("format") String format
    ) {
        return adminProblemService.bulkImport(file, format);
    }

    @GetMapping("/submissions")
    public Page<AdminSubmissionDto> getSubmissions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String verdict,
            @RequestParam(required = false) String language,
            @RequestParam(required = false) String userId,
            @RequestParam(required = false) String problemId
    ) {
        return adminSubmissionService.getSubmissions(page, size, verdict, language, userId, problemId);
    }

    @GetMapping("/submissions/{id}")
    public AdminSubmissionDto getSubmissionById(@PathVariable Long id) {
        return adminSubmissionService.getSubmissionById(id);
    }

    @GetMapping("/analytics/overview")
    public AdminAnalyticsOverviewDto getAnalyticsOverview(
            @RequestParam(defaultValue = "30") int days
    ) {
        return adminAnalyticsService.getOverview(days);
    }

    @GetMapping("/analytics/problems/top-hardest")
    public List<ProblemStatsDto> getTopHardestProblems(
            @RequestParam(defaultValue = "10") int limit
    ) {
        return adminAnalyticsService.getTopHardestProblems(limit);
    }

    @GetMapping("/analytics/problems/top-easiest")
    public List<ProblemStatsDto> getTopEasiestProblems(
            @RequestParam(defaultValue = "10") int limit
    ) {
        return adminAnalyticsService.getTopEasiestProblems(limit);
    }

    @GetMapping("/analytics/users/most-active")
    public List<UserActivityDto> getMostActiveUsers(
            @RequestParam(defaultValue = "10") int limit
    ) {
        return adminAnalyticsService.getMostActiveUsers(limit);
    }

    @GetMapping("/tags")
    public List<TagStatsDto> getTags() {
        return adminTagService.getAllTags();
    }

    @GetMapping("/tags/most-attempted")
    public List<TagStatsDto> getMostAttemptedTags() {
        return adminTagService.getMostAttemptedTags();
    }

    @PutMapping("/tags/rename")
    @Transactional
    public ResponseEntity<Map<String, Object>> renameTag(@RequestBody Map<String, String> body) {
        String oldTag = body.get("oldTag");
        String newTag = body.get("newTag");
        int problemsUpdated = adminTagService.renameTag(oldTag, newTag);
        return ResponseEntity.ok(Map.of("problemsUpdated", problemsUpdated));
    }

    @GetMapping("/ai-feedback/stats")
    public AIFeedbackStatsDto getAIFeedbackStats() {
        return adminAIFeedbackService.getStats();
    }

    @PostMapping("/notifications")
    public NotificationDto createNotification(@RequestBody CreateNotificationRequest request) {
        return notificationService.createNotification(request);
    }

    @GetMapping("/notifications/broadcasts")
    public List<NotificationDto> getBroadcastNotifications() {
        return notificationService.getBroadcasts();
    }

    @GetMapping("/settings")
    public SystemSettingsDto getSettings() {
        return adminSettingsService.getSettings();
    }

    @PutMapping("/settings/maintenance")
    public ResponseEntity<Map<String, Object>> setMaintenanceMode(
            @RequestBody Map<String, Boolean> body,
            Authentication authentication
    ) {
        Boolean enabled = body.get("enabled");
        if (enabled == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "enabled field is required");
        }

        adminSettingsService.setMaintenanceMode(enabled);
        String adminUsername = authentication.getName();
        log.info(
                "Maintenance mode {} by admin {} at {}",
                enabled ? "enabled" : "disabled",
                adminUsername,
                LocalDateTime.now()
        );

        return ResponseEntity.ok(Map.of(
                "maintenanceMode", enabled,
                "message", enabled ? "Maintenance mode enabled" : "Maintenance mode disabled"
        ));
    }

    private AdminUserDto toAdminUserDto(User user) {
        UserProgress progress = userProgressRepository.findByUserId(user.getId()).orElse(null);

        return new AdminUserDto(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getRole().name(),
                user.getSkillLevel(),
                user.getCreatedAt(),
                progress != null ? progress.getTotalSubmissions() : 0,
                progress != null ? progress.getProblemsSolved() : 0,
                progress != null ? progress.getCurrentStreak() : 0,
                progress != null ? progress.getAcceptanceRate() : 0.0,
                progress != null ? progress.getAlgorithmRating() : 800
        );
    }

    private RoleChangeLogDto toRoleChangeLogDto(RoleChangeLog log) {
        return new RoleChangeLogDto(
                log.getTargetUserId(),
                log.getTargetUsername(),
                log.getOldRole(),
                log.getNewRole(),
                log.getChangedByAdminId(),
                log.getChangedByAdminUsername(),
                log.getChangedAt()
        );
    }

    private String getUserIdFromAuth(Authentication authentication) {
        String username = authentication.getName();
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found"))
                .getId();
    }
}
