package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.progress.*;
import com.AlgoGym.backend.model.UserProgress;
import com.AlgoGym.backend.model.UserTagStats;
import com.AlgoGym.backend.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.UserKcMastery;
import com.AlgoGym.backend.model.UserWeaknessSummary;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProgressService {

    private final SubmissionRepository submissionRepository;
    private final ProblemRepository problemRepository;
    private final UserProgressRepository userProgressRepository;
    private final UserTagStatsRepository userTagStatsRepository;
    private final UserWeaknessSummaryRepository userWeaknessSummaryRepository;
    private final UserKcMasteryRepository userKcMasteryRepository;
    private final GroqLLMService groqLLMService;

    // Fixed axes — top 5 most common tags in the database
    private static final List<String> RADAR_TAGS = List.of(
            "implementation", "greedy", "math", "dp", "graphs"
    );

    public ProgressResponse getProgress(String userId) {
        List<HeatmapEntryDto> heatmap = getHeatmap(userId);
        RadarDataDto radarData        = getRadarData(userId);
        DifficultyMasteryDto mastery  = getDifficultyMastery(userId);
        String aiInsight              = generateAiInsight(userId);

        return new ProgressResponse(heatmap, radarData, mastery, aiInsight);
    }

    private String generateAiInsight(String userId) {
        var page = submissionRepository
                .findByUserIdOrderBySubmittedAtDesc(userId, PageRequest.of(0, 1));
        Submission latest = page.hasContent() ? page.getContent().get(0) : null;

        List<String> weakTopics = loadTopWeakTopics(userId);
        if (latest == null && weakTopics.isEmpty()) {
            return "Keep solving problems to unlock personalized AI insights.";
        }

        Problem problem = null;
        if (latest != null) {
            problem = problemRepository.findById(latest.getProblemId()).orElse(null);
        }

        List<String> weakWithMastery = weakTopics.stream()
                .map(kc -> formatWeakTopic(userId, kc))
                .collect(Collectors.toList());

        return groqLLMService.generateProgressInsight(latest, problem, weakWithMastery);
    }

    private List<String> loadTopWeakTopics(String userId) {
        return userWeaknessSummaryRepository.findByUserId(userId)
                .map(UserWeaknessSummary::getWeakest5)
                .map(this::parseWeakest5)
                .orElse(List.of());
    }

    private List<String> parseWeakest5(String weakest5) {
        if (weakest5 == null || weakest5.isBlank()) {
            return List.of();
        }
        return Arrays.stream(weakest5.split(";"))
                .map(String::trim)
                .filter(s -> !s.isBlank())
                .limit(5)
                .collect(Collectors.toList());
    }

    private String formatWeakTopic(String userId, String kc) {
        String label = humanize(kc);
        Optional<UserKcMastery> row = userKcMasteryRepository
                .findByUserIdAndKcNameIgnoreCase(userId, kc.trim());
        if (row.isEmpty() || row.get().getMastery() == null) {
            return label;
        }
        int pct = (int) Math.round(row.get().getMastery() * 100.0);
        return label + " (" + pct + "% mastery)";
    }

    private String humanize(String key) {
        if (key == null || key.isBlank()) {
            return "General";
        }
        return Arrays.stream(key.replace("_", " ").split("\\s+"))
                .filter(s -> !s.isBlank())
                .map(s -> Character.toUpperCase(s.charAt(0)) + s.substring(1).toLowerCase(Locale.ROOT))
                .collect(Collectors.joining(" "));
    }

    // ── Heatmap ───────────────────────────────────────────────────────────────
    private List<HeatmapEntryDto> getHeatmap(String userId) {
        // Keep this aligned with the 365-day window shown on the frontend.
        LocalDateTime oneYearAgo = LocalDateTime.now().minusDays(364);
        List<Object[]> rows = submissionRepository.findDailySubmissionCounts(userId, oneYearAgo);

        List<HeatmapEntryDto> heatmap = new ArrayList<>();
        for (Object[] row : rows) {
            String date   = row[0].toString();
            Integer count = ((Number) row[1]).intValue();
            heatmap.add(new HeatmapEntryDto(date, count));
        }
        return heatmap;
    }

    // ── Radar ─────────────────────────────────────────────────────────────────
    private RadarDataDto getRadarData(String userId) {
        // Fetch only the 5 fixed tags for this user
        List<UserTagStats> allStats = userTagStatsRepository
                .findByUserIdOrderBySubmissionsDesc(userId);

        // Map tag → stats for quick lookup
        Map<String, UserTagStats> statsMap = allStats.stream()
                .collect(Collectors.toMap(
                        s -> s.getTag().toLowerCase(),
                        s -> s,
                        (a, b) -> a
                ));

        List<RadarPointDto> points = RADAR_TAGS.stream()
                .map(tag -> {
                    UserTagStats stat = statsMap.get(tag);
                    if (stat == null || stat.getSubmissions() == 0) {
                        return new RadarPointDto(tag, 0.0, 0, 0);
                    }
                    double rate = Math.round(
                            (stat.getSolved() * 100.0 / stat.getSubmissions()) * 10.0
                    ) / 10.0;
                    return new RadarPointDto(tag, rate, stat.getSolved(), stat.getSubmissions());
                })
                .collect(Collectors.toList());

        return new RadarDataDto(points);
    }

    // ── Difficulty Mastery ────────────────────────────────────────────────────
    private DifficultyMasteryDto getDifficultyMastery(String userId) {
        UserProgress progress = userProgressRepository.findByUserId(userId)
                .orElse(new UserProgress());

        Long totalEasy   = problemRepository.countEasyProblems();
        Long totalMedium = problemRepository.countMediumProblems();
        Long totalHard   = problemRepository.countHardProblems();

        return new DifficultyMasteryDto(
                progress.getEasySolved()   != null ? progress.getEasySolved()   : 0,
                progress.getMediumSolved() != null ? progress.getMediumSolved() : 0,
                progress.getHardSolved()   != null ? progress.getHardSolved()   : 0,
                totalEasy,
                totalMedium,
                totalHard
        );
    }
}