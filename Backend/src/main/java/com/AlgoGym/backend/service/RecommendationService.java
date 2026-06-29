package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.recommendations.RecommendationItemDto;
import com.AlgoGym.backend.dto.recommendations.RecommendationsResponse;
import com.AlgoGym.backend.dto.recommendations.WeakAreaRecommendationsDto;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Recommendation;
import com.AlgoGym.backend.model.UserKcMastery;
import com.AlgoGym.backend.model.UserWeaknessSummary;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.RecommendationRepository;
import com.AlgoGym.backend.repository.UserKcMasteryRepository;
import com.AlgoGym.backend.repository.UserWeaknessSummaryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RecommendationService {

    private static final Pattern WEAK_KC_REASON = Pattern.compile(
            "Targets weak KC:\\s*([^(.]+)",
            Pattern.CASE_INSENSITIVE
    );

    private static final List<String> ACCENTS = List.of(
            "#a855f7", "#6366f1", "#d946ef", "#10b981", "#3b82f6", "#f59e0b", "#0ea5e9"
    );

    private final RecommendationRepository recommendationRepository;
    private final ProblemRepository problemRepository;
    private final UserWeaknessSummaryRepository userWeaknessSummaryRepository;
    private final UserKcMasteryRepository userKcMasteryRepository;

    public RecommendationsResponse getRecommendationsForUser(String userId) {
        Optional<UserWeaknessSummary> weaknessOpt = userWeaknessSummaryRepository.findByUserId(userId);
        List<UserKcMastery> masteryRows = userKcMasteryRepository.findByUserId(userId);
        Map<String, UserKcMastery> masteryByKc = masteryRows.stream()
                .collect(Collectors.toMap(
                        m -> normalizeKc(m.getKcName()),
                        m -> m,
                        (a, b) -> a
                ));

        List<Recommendation> rows = recommendationRepository.findByUserIdOrderByIdAsc(userId);

        if (rows.isEmpty() && weaknessOpt.isEmpty()) {
            return new RecommendationsResponse(null, 0, 0, List.of());
        }

        Map<String, Problem> problemMap = Map.of();
        if (!rows.isEmpty()) {
            Set<String> problemIds = rows.stream()
                    .map(Recommendation::getProblemId)
                    .collect(Collectors.toSet());
            problemMap = problemRepository.findAllById(problemIds).stream()
                    .collect(Collectors.toMap(Problem::getId, p -> p));
        }

        LocalDateTime lastUpdated = rows.stream()
                .map(Recommendation::getCreatedAt)
                .filter(Objects::nonNull)
                .max(LocalDateTime::compareTo)
                .orElse(null);

        Map<String, List<RecommendationItemDto>> grouped = new LinkedHashMap<>();
        for (Recommendation row : rows) {
            Problem problem = problemMap.get(row.getProblemId());
            String groupKey = resolveGroupKey(row.getReason(), problem);
            grouped.computeIfAbsent(normalizeKc(groupKey), k -> new ArrayList<>())
                    .add(toItemDto(row, problem));
        }

        List<WeakAreaRecommendationsDto> weakAreas;
        if (weaknessOpt.isPresent()) {
            weakAreas = buildWeakAreasFromGppkt(
                    weaknessOpt.get(),
                    masteryByKc,
                    grouped
            );
        } else {
            weakAreas = buildWeakAreasFromRecommendations(grouped);
        }

        return new RecommendationsResponse(
                lastUpdated,
                rows.size(),
                weakAreas.size(),
                weakAreas
        );
    }

    private List<WeakAreaRecommendationsDto> buildWeakAreasFromGppkt(
            UserWeaknessSummary summary,
            Map<String, UserKcMastery> masteryByKc,
            Map<String, List<RecommendationItemDto>> grouped
    ) {
        List<String> orderedKcs = parseWeakest5(summary.getWeakest5());
        List<WeakAreaRecommendationsDto> weakAreas = new ArrayList<>();
        int accentIdx = 0;

        for (String kc : orderedKcs) {
            String key = normalizeKc(kc);
            UserKcMastery mastery = masteryByKc.get(key);
            Integer masteryPct = masteryPct(mastery);
            List<RecommendationItemDto> items = grouped.getOrDefault(key, List.of());

            weakAreas.add(new WeakAreaRecommendationsDto(
                    slugify(kc),
                    humanize(kc),
                    masteryPct,
                    ACCENTS.get(accentIdx % ACCENTS.size()),
                    insightForMastery(kc, masteryPct),
                    items
            ));
            accentIdx++;
        }

        return weakAreas;
    }

    private List<WeakAreaRecommendationsDto> buildWeakAreasFromRecommendations(
            Map<String, List<RecommendationItemDto>> grouped
    ) {
        List<WeakAreaRecommendationsDto> weakAreas = new ArrayList<>();
        int accentIdx = 0;
        for (Map.Entry<String, List<RecommendationItemDto>> entry : grouped.entrySet()) {
            String key = entry.getKey();
            weakAreas.add(new WeakAreaRecommendationsDto(
                    slugify(key),
                    humanize(key),
                    null,
                    ACCENTS.get(accentIdx % ACCENTS.size()),
                    insightForMastery(key, null),
                    entry.getValue()
            ));
            accentIdx++;
        }
        return weakAreas;
    }

    private List<String> parseWeakest5(String weakest5) {
        if (weakest5 == null || weakest5.isBlank()) {
            return List.of();
        }
        return Arrays.stream(weakest5.split(";"))
                .map(String::trim)
                .filter(s -> !s.isBlank())
                .collect(Collectors.toList());
    }

    private Integer masteryPct(UserKcMastery mastery) {
        if (mastery == null || mastery.getMastery() == null) {
            return null;
        }
        return (int) Math.round(mastery.getMastery() * 100.0);
    }

    private String normalizeKc(String kc) {
        if (kc == null) {
            return "";
        }
        return kc.trim().toLowerCase(Locale.ROOT);
    }

    private RecommendationItemDto toItemDto(Recommendation row, Problem problem) {
        String title = problem != null ? problem.getTitle() : row.getProblemId();
        String difficulty = resolveDifficulty(problem);
        String topic = firstTag(problem);

        return new RecommendationItemDto(
                row.getProblemId(),
                title,
                difficulty,
                topic,
                row.getReason(),
                row.getConfidenceScore()
        );
    }

    private String resolveGroupKey(String reason, Problem problem) {
        if (reason != null) {
            Matcher m = WEAK_KC_REASON.matcher(reason);
            if (m.find()) {
                return m.group(1).trim();
            }
        }
        String tag = firstTag(problem);
        return tag != null && !tag.isBlank() ? tag : "general";
    }

    private String firstTag(Problem problem) {
        if (problem == null || problem.getTags() == null || problem.getTags().isEmpty()) {
            return "general";
        }
        return problem.getTags().get(0);
    }

    private String resolveDifficulty(Problem problem) {
        if (problem == null) {
            return "MEDIUM";
        }
        if (problem.getDifficulty() != null && !problem.getDifficulty().isBlank()) {
            return problem.getDifficulty().toUpperCase(Locale.ROOT);
        }
        Long rating = problem.getRating();
        if (rating == null) {
            return "MEDIUM";
        }
        if (rating < 1200) {
            return "EASY";
        }
        if (rating < 1600) {
            return "MEDIUM";
        }
        return "HARD";
    }

    private String insightForMastery(String groupKey, Integer masteryPct) {
        if (masteryPct == null) {
            return "Practice " + humanize(groupKey) + " to strengthen this area.";
        }
        if (masteryPct < 40) {
            return "Low mastery on " + humanize(groupKey) + " — prioritized practice recommended.";
        }
        if (masteryPct < 55) {
            return "Room to grow in " + humanize(groupKey) + " — keep practicing.";
        }
        return "Building strength in " + humanize(groupKey) + ".";
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

    private String slugify(String key) {
        return key.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "-").replaceAll("^-|-$", "");
    }
}
