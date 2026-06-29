package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.dashboard.*;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.UserProgress;
import com.AlgoGym.backend.model.UserTagStats;
import org.springframework.http.HttpStatus;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.UserProgressRepository;
import com.AlgoGym.backend.repository.UserTagStatsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class DashboardService {

    private final UserProgressRepository userProgressRepository;
    private final SubmissionRepository submissionRepository;
    private final ProblemRepository problemRepository;
    private final UserTagStatsRepository userTagStatsRepository;

    public DashboardResponse getDashboard(String userId, String username, int activityPage, int activitySize) {
        UserStatsDto stats              = getUserStats(userId, username);
        List<PerformanceDataDto> perf   = getPerformanceData(userId, 30);
        RecentActivityResponse activity = getRecentActivity(userId, activityPage, activitySize);
        List<FocusAreaDto> focusAreas   = getFocusAreas(userId);

        return new DashboardResponse(stats, perf, activity, focusAreas);
    }

    // ── Stats ─────────────────────────────────────────────────────────────────
    private UserStatsDto getUserStats(String userId, String username) {
        UserProgress progress = userProgressRepository.findByUserId(userId)
                .orElse(defaultProgress(userId));

        String globalRank = calculateGlobalRank(userId);

        // Rating from user_progress — computed on each submission
        Integer algorithmRating = progress.getAlgorithmRating() != null
                ? progress.getAlgorithmRating() : 800;

        // "+4 NEW" — problems first solved in last 24h
        Long newlySolved = submissionRepository.countNewlySolvedSince(
                userId, LocalDateTime.now().minusHours(24)
        );

        // Velocity — week-over-week XP change
        String velocityMessage = calculateVelocityMessage(userId);

        return new UserStatsDto(
                username,
                progress.getProblemsSolved()  != null ? progress.getProblemsSolved()  : 0,
                progress.getEasySolved()      != null ? progress.getEasySolved()      : 0,
                progress.getMediumSolved()    != null ? progress.getMediumSolved()    : 0,
                progress.getHardSolved()      != null ? progress.getHardSolved()      : 0,
                progress.getCurrentStreak()   != null ? progress.getCurrentStreak()   : 0,
                progress.getAcceptanceRate()  != null ? progress.getAcceptanceRate()  : 0.0,
                globalRank,
                algorithmRating,
                newlySolved.intValue(),
                velocityMessage
        );
    }

    private UserProgress defaultProgress(String userId) {
        UserProgress p = new UserProgress();
        p.setUserId(userId);
        p.setProblemsSolved(0);
        p.setEasySolved(0);
        p.setMediumSolved(0);
        p.setHardSolved(0);
        p.setCurrentStreak(0);
        p.setAcceptanceRate(0.0);
        p.setAlgorithmRating(800);
        return p;
    }

    // ── Global Rank ───────────────────────────────────────────────────────────
    private String calculateGlobalRank(String userId) {
        Long rank       = userProgressRepository.getUserRank(userId);
        Long totalUsers = userProgressRepository.getTotalUsers();

        if (rank == null || totalUsers == null || totalUsers == 0) return "N/A";

        double percentage = (rank * 100.0) / totalUsers;
        if (percentage <= 5)  return "TOP 5%";
        if (percentage <= 10) return "TOP 10%";
        return "#" + rank;
    }

    // ── Velocity ──────────────────────────────────────────────────────────────
    private String calculateVelocityMessage(String userId) {
        LocalDateTime now           = LocalDateTime.now();
        LocalDateTime thisWeekStart = now.minusDays(7);
        LocalDateTime lastWeekStart = now.minusDays(14);

        List<Submission> thisWeek = submissionRepository.findAcceptedBetween(userId, thisWeekStart, now);
        List<Submission> lastWeek = submissionRepository.findAcceptedBetween(userId, lastWeekStart, thisWeekStart);

        int thisXP = calculateXPFromSubmissions(thisWeek);
        int lastXP = calculateXPFromSubmissions(lastWeek);

        if (lastXP == 0 && thisXP == 0) return "Start solving to track your progress!";
        if (lastXP == 0) return "Great start! Keep the momentum going.";

        double change = ((thisXP - lastXP) * 100.0) / lastXP;

        if (change > 0)      return "Your analytical velocity increased by " + Math.round(change) + "% this week.";
        else if (change < 0) return "Your analytical velocity dropped by " + Math.abs(Math.round(change)) + "% this week.";
        else                 return "Your analytical velocity is steady this week.";
    }

    // ── Performance Chart (Cumulative XP) ────────────────────────────────────
    private List<PerformanceDataDto> getPerformanceData(String userId, int days) {
        LocalDateTime startDate = LocalDateTime.now().minusDays(days);
        List<Submission> submissions = submissionRepository.findRecentSubmissions(userId, startDate);

        // Batch load all problems to avoid N+1 queries
        Set<String> problemIds = submissions.stream()
                .map(Submission::getProblemId)
                .collect(Collectors.toSet());

        Map<String, Problem> problemMap = problemRepository.findAllById(problemIds)
                .stream()
                .collect(Collectors.toMap(Problem::getId, p -> p));

        Map<LocalDate, List<Submission>> byDate = submissions.stream()
                .collect(Collectors.groupingBy(s -> s.getSubmittedAt().toLocalDate()));

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMM dd");
        List<PerformanceDataDto> result = new ArrayList<>();
        int cumulativeXP = 0;

        for (int i = days - 1; i >= 0; i--) {
            LocalDate date = LocalDate.now().minusDays(i);
            List<Submission> daySubmissions = byDate.getOrDefault(date, List.of());

            int dailyXP = daySubmissions.stream()
                    .filter(s -> "ACCEPTED".equals(s.getVerdict()))
                    .mapToInt(s -> {
                        Problem p = problemMap.get(s.getProblemId());
                        if (p == null || p.getRating() == null) return 100;
                        long rating = p.getRating();
                        if (rating < 1200) return 100;
                        if (rating < 1600) return 200;
                        return 400;
                    })
                    .sum();

            cumulativeXP += dailyXP;

            result.add(new PerformanceDataDto(
                    date.format(formatter),
                    cumulativeXP,
                    daySubmissions.size()
            ));
        }

        return result;
    }

    // ── Focus Areas ───────────────────────────────────────────────────────────
    private List<FocusAreaDto> getFocusAreas(String userId) {
        List<UserTagStats> tagStats = userTagStatsRepository
                .findByUserIdOrderBySubmissionsDesc(userId);

        if (tagStats.isEmpty()) return List.of();

        Long total = userTagStatsRepository.getTotalTagSubmissions(userId);
        if (total == null || total == 0) return List.of();

        return tagStats.stream()
                .limit(10)
                .map(stat -> new FocusAreaDto(
                        stat.getTag(),
                        stat.getSubmissions(),
                        Math.round((stat.getSubmissions() * 100.0 / total) * 10.0) / 10.0,
                        stat.getSolved()
                ))
                .collect(Collectors.toList());
    }

    // ── Recent Activity ───────────────────────────────────────────────────────
    private RecentActivityResponse getRecentActivity(String userId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Submission> submissionPage = submissionRepository
                .findByUserIdOrderBySubmittedAtDesc(userId, pageable);

        Set<String> problemIds = submissionPage.getContent().stream()
                .map(Submission::getProblemId)
                .collect(Collectors.toSet());

        Map<String, Problem> problemMap = problemRepository.findAllById(problemIds)
                .stream()
                .collect(Collectors.toMap(Problem::getId, p -> p));

        List<ActivityDto> activities = submissionPage.getContent().stream()
                .map(s -> mapToActivityDto(s, problemMap.get(s.getProblemId())))
                .collect(Collectors.toList());

        return new RecentActivityResponse(
                activities,
                submissionPage.getTotalPages(),
                submissionPage.getNumber(),
                submissionPage.getTotalElements()
        );
    }

    private ActivityDto mapToActivityDto(Submission submission, Problem problem) {
        String title      = problem != null ? problem.getTitle() : "Unknown Problem";
        String difficulty = problem != null ? getDifficultyFromRating(problem) : "MEDIUM";
        String tag        = problem != null && problem.getTags() != null && !problem.getTags().isEmpty()
                ? problem.getTags().get(0) : "";

        String runtime = null;
        if (submission.getExecutionTimeMs() != null) {
            runtime = String.format("%.0fms", submission.getExecutionTimeMs());
        }
        String memory = null;
        if (submission.getMemoryUsedKb() != null) {
            memory = String.format("%.1fMB", submission.getMemoryUsedKb() / 1024.0);
        }
        String language = submission.getLanguageName();
        if (language != null && language.isBlank()) {
            language = null;
        }

        return new ActivityDto(
                submission.getProblemId(),
                submission.getId(),
                title,
                difficulty,
                submission.getVerdict(),
                submission.getSubmittedAt(),
                tag,
                runtime,
                memory,
                language,
                submission.getPassedTests(),
                submission.getTotalTests()
        );
    }

    public SubmissionSourceDto getSubmissionSource(String userId, Long submissionId) {
        Submission submission = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Submission not found"));

        if (!userId.equals(submission.getUserId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not your submission");
        }

        Problem problem = problemRepository.findById(submission.getProblemId()).orElse(null);
        String problemTitle = problem != null ? problem.getTitle() : "Unknown Problem";

        String language = submission.getLanguageName();
        if (language != null && language.isBlank()) {
            language = null;
        }

        return new SubmissionSourceDto(
                submission.getSourceCode(),
                language,
                problemTitle
        );
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    private int calculateXPFromSubmissions(List<Submission> submissions) {
        if (submissions == null || submissions.isEmpty()) return 0;

        Set<String> ids = submissions.stream()
                .map(Submission::getProblemId)
                .collect(Collectors.toSet());

        Map<String, Problem> problemMap = problemRepository.findAllById(ids)
                .stream()
                .collect(Collectors.toMap(Problem::getId, p -> p));

        return submissions.stream().mapToInt(s -> {
            Problem p = problemMap.get(s.getProblemId());
            if (p == null || p.getRating() == null) return 100;
            long rating = p.getRating();
            if (rating < 1200) return 100;
            if (rating < 1600) return 200;
            return 400;
        }).sum();
    }

    private String getDifficultyFromRating(Problem problem) {
        Long rating = problem.getRating();
        if (rating == null) return "MEDIUM";
        if (rating < 1200) return "EASY";
        if (rating < 1600) return "MEDIUM";
        return "HARD";
    }
}