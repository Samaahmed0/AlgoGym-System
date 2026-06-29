package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.admin.AdminProblemDto;
import com.AlgoGym.backend.dto.admin.BulkImportResultDto;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import lombok.RequiredArgsConstructor;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AdminProblemService {

    private final ProblemRepository problemRepository;
    private final SubmissionRepository submissionRepository;
    private final AIFeedbackRepository aiFeedbackRepository;
    private final EntityManager entityManager;
    private final ObjectMapper objectMapper;

    public Page<AdminProblemDto> getAdminProblems(
            int page,
            int size,
            String search,
            String difficulty,
            String visible
    ) {
        StringBuilder where = new StringBuilder(" WHERE 1=1 ");
        List<Object> params = new ArrayList<>();
        int paramIndex = 1;

        if (search != null && !search.isBlank()) {
            where.append(" AND LOWER(p.title) LIKE LOWER(?").append(paramIndex++).append(")");
            params.add("%" + search + "%");
        }

        if (difficulty != null && !difficulty.isBlank()) {
            long[] range = ratingRangeForDifficulty(difficulty);
            if (range != null) {
                where.append(" AND p.rating >= ?").append(paramIndex++)
                        .append(" AND p.rating <= ?").append(paramIndex++);
                params.add(range[0]);
                params.add(range[1]);
            }
        }

        String visibleFilter = visible == null ? "all" : visible.toLowerCase(Locale.ROOT);
        if ("visible".equals(visibleFilter)) {
            where.append(" AND p.is_visible = true");
        } else if ("hidden".equals(visibleFilter)) {
            where.append(" AND p.is_visible = false");
        }

        String countQuery = "SELECT COUNT(*) FROM \"Problems\" p" + where;
        Query countQ = entityManager.createNativeQuery(countQuery);
        bindParams(countQ, params);
        long total = ((Number) countQ.getSingleResult()).longValue();

        String baseQuery = "SELECT * FROM \"Problems\" p" + where + " ORDER BY p.title ASC";
        Query dataQ = entityManager.createNativeQuery(baseQuery, Problem.class);
        bindParams(dataQ, params);
        dataQ.setFirstResult(page * size);
        dataQ.setMaxResults(size);

        @SuppressWarnings("unchecked")
        List<Problem> problems = dataQ.getResultList();
        List<String> problemIds = problems.stream().map(Problem::getId).toList();
        Map<String, long[]> submissionStats = loadSubmissionStats(problemIds);

        Pageable pageable = PageRequest.of(page, size);
        List<AdminProblemDto> dtos = problems.stream()
                .map(problem -> toAdminProblemDto(problem, submissionStats))
                .toList();

        return new PageImpl<>(dtos, pageable, total);
    }

    public AdminProblemDto updateVisibility(String id, boolean visible) {
        Problem problem = problemRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Problem not found"));
        problem.setIsVisible(visible);
        problemRepository.save(problem);
        return toAdminProblemDto(problem, loadSubmissionStats(List.of(id)));
    }

    @Transactional
    public void deleteProblem(String id) {
        if (!problemRepository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Problem not found");
        }
        aiFeedbackRepository.deleteByProblemId(id);
        submissionRepository.deleteByProblemId(id);
        problemRepository.deleteById(id);
    }

    @Transactional
    public BulkImportResultDto bulkImport(MultipartFile file, String format) {
        if (file == null || file.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is required");
        }

        String normalizedFormat = format == null ? "" : format.toLowerCase(Locale.ROOT);
        return switch (normalizedFormat) {
            case "json" -> importFromJson(file);
            case "csv" -> importFromCsv(file);
            default -> throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST, "Format must be 'json' or 'csv'");
        };
    }

    private BulkImportResultDto importFromJson(MultipartFile file) {
        BulkImportResultDto result = new BulkImportResultDto();
        result.setErrors(new ArrayList<>());

        try {
            JsonNode root = objectMapper.readTree(file.getInputStream());
            if (!root.isArray()) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "JSON must be an array of problems");
            }

            int row = 0;
            for (JsonNode node : root) {
                row++;
                processImportNode(node, "Row " + row, result);
            }
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid JSON file: " + e.getMessage());
        }

        return result;
    }

    private BulkImportResultDto importFromCsv(MultipartFile file) {
        BulkImportResultDto result = new BulkImportResultDto();
        result.setErrors(new ArrayList<>());

        try (CSVParser parser = CSVFormat.DEFAULT.builder()
                .setHeader()
                .setSkipHeaderRecord(true)
                .build()
                .parse(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {

            int row = 1;
            for (CSVRecord record : parser) {
                row++;
                processCsvRecord(record, "Row " + row, result);
            }
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid CSV file: " + e.getMessage());
        }

        return result;
    }

    private void processCsvRecord(CSVRecord record, String label, BulkImportResultDto result) {
        Map<String, String> fields = new HashMap<>();
        record.toMap().forEach((key, value) -> fields.put(key, value));
        processImportNode(objectMapper.valueToTree(fields), label, result);
    }

    private void processImportNode(JsonNode node, String label, BulkImportResultDto result) {
        String id = textOrNull(node, "id");
        if (id == null || id.isBlank()) {
            result.setFailed(result.getFailed() + 1);
            result.getErrors().add(label + ": missing id");
            return;
        }

        if (problemRepository.existsById(id)) {
            result.setSkipped(result.getSkipped() + 1);
            return;
        }

        String title = textOrNull(node, "title");
        String description = textOrNull(node, "description");
        String ratingText = textOrNull(node, "rating");

        if (title == null || title.isBlank()) {
            result.setFailed(result.getFailed() + 1);
            result.getErrors().add(label + ": missing title");
            return;
        }
        if (description == null || description.isBlank()) {
            result.setFailed(result.getFailed() + 1);
            result.getErrors().add(label + ": missing description");
            return;
        }
        if (ratingText == null || ratingText.isBlank()) {
            result.setFailed(result.getFailed() + 1);
            result.getErrors().add(label + ": missing rating");
            return;
        }

        Long rating;
        try {
            rating = Long.parseLong(ratingText.trim());
        } catch (NumberFormatException e) {
            result.setFailed(result.getFailed() + 1);
            result.getErrors().add(label + ": invalid rating");
            return;
        }

        Problem problem = new Problem();
        problem.setId(id);
        problem.setTitle(title);
        problem.setDescription(description);
        problem.setRating(rating);
        problem.setTags(parseTags(node.get("tags")));
        problem.setTimeLimit(parseDouble(node, "timeLimit"));
        problem.setMemoryLimit(parseLong(node, "memoryLimit"));
        problem.setIsVisible(true);

        problemRepository.save(problem);
        result.setImported(result.getImported() + 1);
    }

    private List<String> parseTags(JsonNode tagsNode) {
        if (tagsNode == null || tagsNode.isNull()) {
            return List.of();
        }
        if (tagsNode.isArray()) {
            List<String> tags = new ArrayList<>();
            tagsNode.forEach(tag -> tags.add(tag.asText().trim()));
            return tags;
        }
        String tagsText = tagsNode.asText("");
        if (tagsText.isBlank()) {
            return List.of();
        }
        return List.of(tagsText.split(",")).stream()
                .map(String::trim)
                .filter(tag -> !tag.isEmpty())
                .toList();
    }

    private String textOrNull(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull()) {
            return null;
        }
        return value.asText();
    }

    private Double parseDouble(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull() || value.asText().isBlank()) {
            return null;
        }
        return Double.parseDouble(value.asText().trim());
    }

    private Long parseLong(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull() || value.asText().isBlank()) {
            return null;
        }
        return Long.parseLong(value.asText().trim());
    }

    private Map<String, long[]> loadSubmissionStats(List<String> problemIds) {
        Map<String, long[]> stats = new HashMap<>();
        if (problemIds == null || problemIds.isEmpty()) {
            return stats;
        }

        List<Object[]> rows = submissionRepository.countSubmissionStatsByProblemIds(problemIds);
        for (Object[] row : rows) {
            String problemId = (String) row[0];
            long total = ((Number) row[1]).longValue();
            long accepted = row[2] == null ? 0L : ((Number) row[2]).longValue();
            stats.put(problemId, new long[]{total, accepted});
        }
        return stats;
    }

    private AdminProblemDto toAdminProblemDto(Problem problem, Map<String, long[]> submissionStats) {
        long[] counts = submissionStats.getOrDefault(problem.getId(), new long[]{0L, 0L});
        long totalSubmissions = counts[0];
        long acceptedSubmissions = counts[1];
        double acceptanceRate = totalSubmissions == 0
                ? 0.0
                : Math.round((acceptedSubmissions * 1000.0) / totalSubmissions) / 10.0;

        return new AdminProblemDto(
                problem.getId(),
                problem.getTitle(),
                problem.getRating(),
                problem.getTags(),
                problem.getTimeLimit(),
                problem.getMemoryLimit(),
                problem.getIsVisible() != null ? problem.getIsVisible() : true,
                totalSubmissions,
                acceptanceRate
        );
    }

    private long[] ratingRangeForDifficulty(String difficulty) {
        return switch (difficulty.toLowerCase(Locale.ROOT)) {
            case "easy" -> new long[]{0L, 1199L};
            case "medium" -> new long[]{1200L, 1599L};
            case "hard" -> new long[]{1600L, 1999L};
            case "expert" -> new long[]{2000L, 5000L};
            default -> null;
        };
    }

    private void bindParams(Query query, List<Object> params) {
        for (int i = 0; i < params.size(); i++) {
            query.setParameter(i + 1, params.get(i));
        }
    }
}
