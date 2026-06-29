package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.admin.AIFeedbackStatsDto;
import com.AlgoGym.backend.dto.admin.ErrorTypeCountDto;
import com.AlgoGym.backend.dto.admin.ProblematicProblemDto;
import com.AlgoGym.backend.dto.admin.RecentFeedbackDto;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AdminAIFeedbackService {

    private final AIFeedbackRepository aiFeedbackRepository;
    private final SubmissionRepository submissionRepository;

    public AIFeedbackStatsDto getStats() {
        LocalDateTime weekAgo = LocalDateTime.now().minusDays(7);
        Long totalFeedbackThisWeek = aiFeedbackRepository.countByCreatedAtAfter(weekAgo);
        Long totalFeedbackAllTime = aiFeedbackRepository.count();

        List<ErrorTypeCountDto> errorTypeBreakdown = aiFeedbackRepository.findErrorTypeBreakdown().stream()
                .map(row -> toErrorTypeCountDto(row, totalFeedbackAllTime))
                .toList();

        List<Object[]> problematicRows = aiFeedbackRepository.findMostProblematicProblems();
        List<String> problemIds = problematicRows.stream()
                .map(row -> (String) row[0])
                .toList();
        Map<String, Long> submissionCountsByProblem = loadSubmissionCounts(problemIds);

        List<ProblematicProblemDto> problemsNeedingReview = problematicRows.stream()
                .map(row -> toProblematicProblemDto(row, submissionCountsByProblem))
                .toList();

        List<RecentFeedbackDto> recentFeedback = aiFeedbackRepository.findRecentFeedbackWithDetails().stream()
                .map(this::toRecentFeedbackDto)
                .toList();

        return new AIFeedbackStatsDto(
                totalFeedbackThisWeek,
                totalFeedbackAllTime,
                errorTypeBreakdown,
                problemsNeedingReview,
                recentFeedback
        );
    }

    private ErrorTypeCountDto toErrorTypeCountDto(Object[] row, long totalAllTime) {
        String errorType = row[0] != null ? row[0].toString() : "UNKNOWN";
        long count = toLong(row[1]);
        double percentage = totalAllTime == 0
                ? 0.0
                : Math.round((count * 1000.0) / totalAllTime) / 10.0;
        return new ErrorTypeCountDto(errorType, count, percentage);
    }

    private ProblematicProblemDto toProblematicProblemDto(
            Object[] row,
            Map<String, Long> submissionCountsByProblem
    ) {
        String problemId = (String) row[0];
        String problemTitle = (String) row[1];
        long helpRequests = toLong(row[2]);
        long totalSubmissions = submissionCountsByProblem.getOrDefault(problemId, toLong(row[3]));
        double helpRequestRate = totalSubmissions == 0
                ? 0.0
                : Math.round((helpRequests * 1000.0) / totalSubmissions) / 10.0;

        return new ProblematicProblemDto(
                problemId,
                problemTitle,
                helpRequests,
                totalSubmissions,
                helpRequestRate
        );
    }

    private RecentFeedbackDto toRecentFeedbackDto(Object[] row) {
        return new RecentFeedbackDto(
                toLong(row[0]),
                toLong(row[1]),
                (String) row[2],
                (String) row[3],
                row[4] != null ? row[4].toString() : null,
                (String) row[5],
                toLocalDateTime(row[6])
        );
    }

    private Map<String, Long> loadSubmissionCounts(List<String> problemIds) {
        Map<String, Long> counts = new HashMap<>();
        if (problemIds.isEmpty()) {
            return counts;
        }
        for (Object[] row : submissionRepository.countSubmissionStatsByProblemIds(problemIds)) {
            counts.put((String) row[0], toLong(row[1]));
        }
        return counts;
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

    private LocalDateTime toLocalDateTime(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof LocalDateTime localDateTime) {
            return localDateTime;
        }
        if (value instanceof Timestamp timestamp) {
            return timestamp.toLocalDateTime();
        }
        throw new IllegalArgumentException("Unsupported date type: " + value.getClass());
    }
}
