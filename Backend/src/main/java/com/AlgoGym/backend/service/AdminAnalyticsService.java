package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.admin.AdminAnalyticsOverviewDto;
import com.AlgoGym.backend.dto.admin.DailyCountDto;
import com.AlgoGym.backend.dto.admin.LanguageStatsDto;
import com.AlgoGym.backend.dto.admin.ProblemStatsDto;
import com.AlgoGym.backend.dto.admin.SkillLevelCountDto;
import com.AlgoGym.backend.dto.admin.UserActivityDto;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.UserProgressRepository;
import com.AlgoGym.backend.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.sql.Date;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AdminAnalyticsService {

    private static final long MIN_PROBLEM_SUBMISSIONS = 10L;

    private final SubmissionRepository submissionRepository;
    private final UserRepository userRepository;
    private final UserProgressRepository userProgressRepository;

    public AdminAnalyticsOverviewDto getOverview(int days) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(days - 1L);
        LocalDateTime since = start.atStartOfDay();

        List<DailyCountDto> dailySubmissions = fillDailyGaps(
                submissionRepository.findGlobalDailySubmissionCounts(since)
                        .stream()
                        .map(this::toDailyCountDto)
                        .toList(),
                start,
                end
        );

        List<DailyCountDto> dailyRegistrations = fillDailyGaps(
                userRepository.findDailyRegistrationCounts(since)
                        .stream()
                        .map(this::toDailyCountDto)
                        .toList(),
                start,
                end
        );

        List<Object[]> languageRows = submissionRepository.findSubmissionsByLanguage();
        long totalLanguageSubmissions = languageRows.stream()
                .mapToLong(row -> toLong(row[1]))
                .sum();
        List<LanguageStatsDto> submissionsByLanguage = languageRows.stream()
                .map(row -> toLanguageStatsDto(row, totalLanguageSubmissions))
                .toList();

        List<SkillLevelCountDto> usersBySkillLevel = userRepository.countBySkillLevel().stream()
                .map(row -> new SkillLevelCountDto(
                        row[0] != null ? row[0].toString() : "unknown",
                        toLong(row[1])
                ))
                .toList();

        return new AdminAnalyticsOverviewDto(
                dailySubmissions,
                dailyRegistrations,
                submissionsByLanguage,
                usersBySkillLevel
        );
    }

    public List<ProblemStatsDto> getTopHardestProblems(int limit) {
        return submissionRepository.findHardestProblemsByAcceptanceRate(MIN_PROBLEM_SUBMISSIONS, limit)
                .stream()
                .map(this::toProblemStatsDto)
                .toList();
    }

    public List<ProblemStatsDto> getTopEasiestProblems(int limit) {
        return submissionRepository.findEasiestProblemsByAcceptanceRate(MIN_PROBLEM_SUBMISSIONS, limit)
                .stream()
                .map(this::toProblemStatsDto)
                .toList();
    }

    public List<UserActivityDto> getMostActiveUsers(int limit) {
        return userProgressRepository.findMostActiveUsers(limit).stream()
                .map(this::toUserActivityDto)
                .toList();
    }

    private DailyCountDto toDailyCountDto(Object[] row) {
        return new DailyCountDto(formatDate(row[0]), toLong(row[1]));
    }

    private List<DailyCountDto> fillDailyGaps(List<DailyCountDto> sparse, LocalDate start, LocalDate end) {
        Map<String, Long> countsByDate = new HashMap<>();
        for (DailyCountDto entry : sparse) {
            if (entry.getDate() != null) {
                countsByDate.put(entry.getDate(), entry.getCount() != null ? entry.getCount() : 0L);
            }
        }

        List<DailyCountDto> filled = new ArrayList<>();
        for (LocalDate day = start; !day.isAfter(end); day = day.plusDays(1)) {
            String key = day.toString();
            filled.add(new DailyCountDto(key, countsByDate.getOrDefault(key, 0L)));
        }
        return filled;
    }

    private LanguageStatsDto toLanguageStatsDto(Object[] row, long totalSubmissions) {
        String language = row[0] != null ? row[0].toString() : "unknown";
        long submissions = toLong(row[1]);
        double percentage = totalSubmissions == 0
                ? 0.0
                : Math.round((submissions * 1000.0) / totalSubmissions) / 10.0;
        return new LanguageStatsDto(language, submissions, percentage);
    }

    private ProblemStatsDto toProblemStatsDto(Object[] row) {
        String problemId = (String) row[0];
        String title = (String) row[1];
        Long rating = toLong(row[2]);
        long totalSubmissions = toLong(row[3]);
        long accepted = toLong(row[4]);
        double acceptanceRate = totalSubmissions == 0
                ? 0.0
                : Math.round((accepted * 1000.0) / totalSubmissions) / 10.0;

        return new ProblemStatsDto(
                problemId,
                title,
                totalSubmissions,
                accepted,
                acceptanceRate,
                difficultyFromRating(rating)
        );
    }

    private UserActivityDto toUserActivityDto(Object[] row) {
        return new UserActivityDto(
                (String) row[0],
                (String) row[1],
                toInteger(row[2]),
                toDouble(row[3]),
                toInteger(row[4]),
                toInteger(row[5])
        );
    }

    private String difficultyFromRating(Long rating) {
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

    private String formatDate(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof LocalDate localDate) {
            return localDate.toString();
        }
        if (value instanceof Date sqlDate) {
            return sqlDate.toLocalDate().toString();
        }
        if (value instanceof java.util.Date utilDate) {
            return new Date(utilDate.getTime()).toLocalDate().toString();
        }
        return value.toString();
    }

    private Long toLong(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        return Long.parseLong(value.toString());
    }

    private Integer toInteger(Object value) {
        if (value == null) {
            return 0;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        return Integer.parseInt(value.toString());
    }

    private Double toDouble(Object value) {
        if (value == null) {
            return 0.0;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return Double.parseDouble(value.toString());
    }
}
