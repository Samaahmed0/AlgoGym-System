package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.admin.TagStatsDto;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.UserTagStatsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AdminTagService {

    private final ProblemRepository problemRepository;
    private final UserTagStatsRepository userTagStatsRepository;

    public List<TagStatsDto> getAllTags() {
        return mergeTagStats(loadProblemTagCounts(), loadUserTagTotals()).stream()
                .sorted(Comparator.comparing(TagStatsDto::getProblemCount, Comparator.nullsLast(Comparator.reverseOrder()))
                        .thenComparing(TagStatsDto::getTag))
                .toList();
    }

    public List<TagStatsDto> getMostAttemptedTags() {
        Map<String, long[]> userTotals = loadUserTagTotals();
        Map<String, Long> problemCounts = loadProblemTagCounts();

        return userTotals.entrySet().stream()
                .map(entry -> new TagStatsDto(
                        entry.getKey(),
                        problemCounts.getOrDefault(entry.getKey(), 0L),
                        entry.getValue()[0],
                        entry.getValue()[1]
                ))
                .sorted(Comparator.comparing(TagStatsDto::getTotalUserSubmissions, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(20)
                .toList();
    }

    @Transactional
    public int renameTag(String oldTag, String newTag) {
        if (oldTag == null || oldTag.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "oldTag is required");
        }
        if (newTag == null || newTag.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "newTag is required");
        }
        if (oldTag.equals(newTag)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "newTag must be different from oldTag");
        }

        Map<String, Long> problemTagCounts = loadProblemTagCounts();
        if (!problemTagCounts.containsKey(oldTag) || problemTagCounts.get(oldTag) == 0) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "oldTag not found");
        }

        Set<String> existingTags = collectAllTagNames(problemTagCounts, loadUserTagTotals());
        if (existingTags.contains(newTag)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "newTag already exists");
        }

        int problemsUpdated = problemRepository.renameTagInProblems(oldTag, newTag);
        userTagStatsRepository.renameTag(oldTag, newTag);
        return problemsUpdated;
    }

    private List<TagStatsDto> mergeTagStats(Map<String, Long> problemCounts, Map<String, long[]> userTotals) {
        Set<String> allTags = new HashSet<>();
        allTags.addAll(problemCounts.keySet());
        allTags.addAll(userTotals.keySet());

        return allTags.stream()
                .map(tag -> {
                    long[] totals = userTotals.getOrDefault(tag, new long[]{0L, 0L});
                    return new TagStatsDto(
                            tag,
                            problemCounts.getOrDefault(tag, 0L),
                            totals[0],
                            totals[1]
                    );
                })
                .collect(Collectors.toList());
    }

    private Map<String, Long> loadProblemTagCounts() {
        Map<String, Long> counts = new HashMap<>();
        for (Object[] row : problemRepository.findAllTagsWithCount()) {
            counts.put((String) row[0], toLong(row[1]));
        }
        return counts;
    }

    private Map<String, long[]> loadUserTagTotals() {
        Map<String, long[]> totals = new HashMap<>();
        for (Object[] row : userTagStatsRepository.findTagSubmissionTotals()) {
            totals.put((String) row[0], new long[]{toLong(row[1]), toLong(row[2])});
        }
        return totals;
    }

    private Set<String> collectAllTagNames(Map<String, Long> problemCounts, Map<String, long[]> userTotals) {
        Set<String> tags = new HashSet<>();
        tags.addAll(problemCounts.keySet());
        tags.addAll(userTotals.keySet());
        return tags;
    }

    private long toLong(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        return Long.parseLong(value.toString());
    }
}
