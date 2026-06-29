package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.ProblemDTO;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ProblemService {

    private final ProblemRepository problemRepository;
    private final SubmissionRepository submissionRepository;
    private final EntityManager entityManager;

    public Page<ProblemDTO> getProblemsByFilters(
            List<String> difficulties,
            List<String> tags,
            String title,
            int page,
            int size
    ) {
        return getProblemsByFilters(difficulties, tags, title, null, null, page, size, false);
    }

    public Page<ProblemDTO> getProblemsByFilters(
            List<String> difficulties,
            List<String> tags,
            String title,
            List<String> statuses,
            String userId,
            int page,
            int size
    ) {
        return getProblemsByFilters(difficulties, tags, title, statuses, userId, page, size, false);
    }

    public Page<ProblemDTO> getProblemsByFilters(
            List<String> difficulties,
            List<String> tags,
            String title,
            List<String> statuses,
            String userId,
            int page,
            int size,
            boolean includeHidden
    ) {
        // Build rating ranges from difficulties
        List<long[]> ratingRanges = new ArrayList<>();
        if (difficulties != null && !difficulties.isEmpty()) {
            for (String difficulty : difficulties) {
                switch (difficulty.toLowerCase()) {
                    case "easy"   -> ratingRanges.add(new long[]{0L,    1199L});
                    case "medium" -> ratingRanges.add(new long[]{1200L, 1599L});
                    case "hard"   -> ratingRanges.add(new long[]{1600L, 1999L});
                    case "expert" -> ratingRanges.add(new long[]{2000L, 5000L});
                }
            }
        }

        // Build WHERE clause dynamically
        StringBuilder where = new StringBuilder(" WHERE 1=1 ");
        List<Object> params = new ArrayList<>();
        int paramIndex = 1;

        if (!includeHidden) {
            where.append(" AND p.is_visible = true");
        }

        // Difficulty — OR across ranges
        if (!ratingRanges.isEmpty()) {
            where.append(" AND (");
            for (int i = 0; i < ratingRanges.size(); i++) {
                if (i > 0) where.append(" OR ");
                where.append("(p.rating >= ?").append(paramIndex++)
                        .append(" AND p.rating <= ?").append(paramIndex++).append(")");
                params.add(ratingRanges.get(i)[0]);
                params.add(ratingRanges.get(i)[1]);
            }
            where.append(")");
        }

        // Tags — OR across tags
        if (tags != null && !tags.isEmpty()) {
            where.append(" AND (");
            for (int i = 0; i < tags.size(); i++) {
                if (i > 0) where.append(" OR ");
                where.append("jsonb_exists(p.tags, ?").append(paramIndex++).append(")");
                params.add(tags.get(i));
            }
            where.append(")");
        }

        // Title search
        if (title != null && !title.isBlank()) {
            where.append(" AND LOWER(p.title) LIKE LOWER(?").append(paramIndex++).append(")");
            params.add("%" + title + "%");
        }

        // Completion status (solved / attempted / unsolved) — derived from submissions
        if (userId != null && !userId.isBlank() && statuses != null && !statuses.isEmpty()) {
            where.append(" AND (");
            boolean first = true;
            for (String status : statuses) {
                String s = status == null ? "" : status.toLowerCase(Locale.ROOT).trim();

                if (!first) where.append(" OR ");
                first = false;

                switch (s) {
                    case "solved" -> {
                        where.append("EXISTS (SELECT 1 FROM submissions sm ")
                                .append("WHERE sm.user_id = ?").append(paramIndex++)
                                .append(" AND sm.problem_id = p.id ")
                                .append(" AND sm.verdict = 'ACCEPTED')");
                        params.add(userId);
                    }
                    case "attempted" -> {
                        where.append("(EXISTS (SELECT 1 FROM submissions sm ")
                                .append("WHERE sm.user_id = ?").append(paramIndex++)
                                .append(" AND sm.problem_id = p.id) ")
                                .append("AND NOT EXISTS (SELECT 1 FROM submissions sm ")
                                .append("WHERE sm.user_id = ?").append(paramIndex++)
                                .append(" AND sm.problem_id = p.id ")
                                .append(" AND sm.verdict = 'ACCEPTED'))");
                        params.add(userId);
                        params.add(userId);
                    }
                    case "unsolved" -> {
                        where.append("NOT EXISTS (SELECT 1 FROM submissions sm ")
                                .append("WHERE sm.user_id = ?").append(paramIndex++)
                                .append(" AND sm.problem_id = p.id)");
                        params.add(userId);
                    }
                }
            }
            where.append(")");
        }

        // Build full queries
        String baseQuery  = "SELECT * FROM \"Problems\" p" + where;
        String countQuery = "SELECT COUNT(*) FROM \"Problems\" p" + where;

        // Count total
        Query countQ = entityManager.createNativeQuery(countQuery);
        for (int i = 0; i < params.size(); i++) {
            countQ.setParameter(i + 1, params.get(i));
        }
        long total = ((Number) countQ.getSingleResult()).longValue();

        // Fetch page
        Query dataQ = entityManager.createNativeQuery(baseQuery, Problem.class);
        for (int i = 0; i < params.size(); i++) {
            dataQ.setParameter(i + 1, params.get(i));
        }
        dataQ.setFirstResult(page * size);
        dataQ.setMaxResults(size);

        @SuppressWarnings("unchecked")
        List<Problem> problems = dataQ.getResultList();

        Pageable pageable = PageRequest.of(page, size);
        Page<Problem> problemPage = new PageImpl<>(problems, pageable, total);

        List<String> problemIds = problems.stream().map(Problem::getId).toList();

        Map<String, Long> totalAttemptsByProblem = new HashMap<>();
        Map<String, Long> acceptedAttemptsByProblem = new HashMap<>();
        if (userId != null && !userId.isBlank() && !problemIds.isEmpty()) {
            List<Submission> submissions = submissionRepository.findByUserIdAndProblemIdIn(userId, problemIds);
            for (Submission sub : submissions) {
                if (sub.getProblemId() == null) continue;
                totalAttemptsByProblem.merge(sub.getProblemId(), 1L, Long::sum);
                if ("ACCEPTED".equals(sub.getVerdict())) {
                    acceptedAttemptsByProblem.merge(sub.getProblemId(), 1L, Long::sum);
                }
            }
        }

        return problemPage.map(problem -> {
            long totalAttempts = totalAttemptsByProblem.getOrDefault(problem.getId(), 0L);
            long acceptedAttempts = acceptedAttemptsByProblem.getOrDefault(problem.getId(), 0L);

            String status;
            double acceptance;

            if (acceptedAttempts > 0) {
                status = "solved";
                acceptance = 100.0;
            } else if (totalAttempts > 0) {
                status = "attempted";
                acceptance = 0.0;
            } else {
                status = "unsolved";
                acceptance = 0.0;
            }

            if (totalAttempts > 0) {
                acceptance = (acceptedAttempts * 100.0) / totalAttempts;
                // Keep it simple: 1 decimal place is enough for the UI
                acceptance = Math.round(acceptance * 10.0) / 10.0;
            }

            return ProblemDTO.builder()
                    .id(problem.getId())
                    .title(problem.getTitle())
                    .description(problem.getDescription())
                    .difficulty(difficultyFromRating(problem.getRating()))
                    .rating(problem.getRating())
                    .tags(problem.getTags())
                    .timeLimit(problem.getTimeLimit())
                    .memoryLimit(problem.getMemoryLimit())
                    .examples(problem.getExamples())
                    .inputFormat(problem.getInputFormat())
                    .outputFormat(problem.getOutputFormat())
                    .note(problem.getNote())
                    .editorial(problem.getEditorial())
                    .status(userId != null && !userId.isBlank() ? status : null)
                    .acceptance(userId != null && !userId.isBlank() ? acceptance : null)
                    .build();
        });
    }

    private String difficultyFromRating(Long rating) {
        if (rating == null) return "MEDIUM";
        if (rating < 1200) return "EASY";
        if (rating < 1600) return "MEDIUM";
        return "HARD";
    }

    public List<String> getAllTags() {
        return problemRepository.findAllTagsWithCount().stream()
                .map(row -> (String) row[0])
                .toList();
    }

    public ProblemDTO getProblemById(String id) {
        Problem problem = problemRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Problem not found: " + id));

        return ProblemDTO.builder()
                .id(problem.getId())
                .title(problem.getTitle())
                .description(problem.getDescription())
                .difficulty(difficultyFromRating(problem.getRating()))
                .rating(problem.getRating())
                .tags(problem.getTags())
                .timeLimit(problem.getTimeLimit())
                .memoryLimit(problem.getMemoryLimit())
                .examples(problem.getExamples())
                .inputFormat(problem.getInputFormat())
                .outputFormat(problem.getOutputFormat())
                .note(problem.getNote())
                .editorial(problem.getEditorial())
                .build();
    }
}