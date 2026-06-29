package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.admin.AdminSubmissionDto;
import com.AlgoGym.backend.model.AIFeedback;
import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.User;
import com.AlgoGym.backend.repository.AIFeedbackRepository;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AdminSubmissionService {

    private final SubmissionRepository submissionRepository;
    private final AIFeedbackRepository aiFeedbackRepository;
    private final UserRepository userRepository;
    private final ProblemRepository problemRepository;

    public Page<AdminSubmissionDto> getSubmissions(
            int page,
            int size,
            String verdict,
            String language,
            String userId,
            String problemId
    ) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Object[]> results = submissionRepository.findAdminSubmissions(
                blankToNull(verdict),
                blankToNull(language),
                blankToNull(userId),
                blankToNull(problemId),
                pageable
        );

        List<Long> submissionIds = results.getContent().stream()
                .map(row -> toLong(row[0]))
                .toList();
        Map<Long, AIFeedback> feedbackBySubmissionId = loadFeedbackBySubmissionIds(submissionIds);

        return results.map(row -> mapListRow(row, feedbackBySubmissionId.get(toLong(row[0]))));
    }

    public AdminSubmissionDto getSubmissionById(Long id) {
        Submission submission = submissionRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Submission not found"));

        User user = userRepository.findById(submission.getUserId())
                .orElse(null);
        Problem problem = problemRepository.findById(submission.getProblemId())
                .orElse(null);
        AIFeedback feedback = aiFeedbackRepository.findBySubmissionId(id).orElse(null);

        return toDetailDto(
                submission,
                user != null ? user.getUsername() : null,
                problem != null ? problem.getTitle() : null,
                feedback
        );
    }

    private AdminSubmissionDto mapListRow(Object[] row, AIFeedback feedback) {
        AdminSubmissionDto dto = new AdminSubmissionDto();
        dto.setId(toLong(row[0]));
        dto.setUserId((String) row[1]);
        dto.setProblemId((String) row[2]);
        dto.setLanguageName((String) row[3]);
        dto.setVerdict((String) row[4]);
        dto.setPassedTests(toInteger(row[5]));
        dto.setTotalTests(toInteger(row[6]));
        dto.setExecutionTimeMs(toDouble(row[7]));
        dto.setMemoryUsedKb(toDouble(row[8]));
        dto.setSubmittedAt(toLocalDateTime(row[9]));
        dto.setUsername((String) row[10]);
        dto.setProblemTitle((String) row[11]);
        dto.setSourceCode(null);
        dto.setTestResults(null);
        applyFeedback(dto, feedback);
        return dto;
    }

    private AdminSubmissionDto toDetailDto(
            Submission submission,
            String username,
            String problemTitle,
            AIFeedback feedback
    ) {
        AdminSubmissionDto dto = new AdminSubmissionDto();
        dto.setId(submission.getId());
        dto.setUserId(submission.getUserId());
        dto.setUsername(username);
        dto.setProblemId(submission.getProblemId());
        dto.setProblemTitle(problemTitle);
        dto.setLanguageName(submission.getLanguageName());
        dto.setVerdict(submission.getVerdict());
        dto.setPassedTests(submission.getPassedTests());
        dto.setTotalTests(submission.getTotalTests());
        dto.setExecutionTimeMs(submission.getExecutionTimeMs());
        dto.setMemoryUsedKb(submission.getMemoryUsedKb());
        dto.setSubmittedAt(submission.getSubmittedAt());
        dto.setSourceCode(submission.getSourceCode());
        dto.setTestResults(submission.getTestResults());
        applyFeedback(dto, feedback);
        return dto;
    }

    private void applyFeedback(AdminSubmissionDto dto, AIFeedback feedback) {
        if (feedback == null) {
            dto.setAiErrorType(null);
            dto.setAiExplanation(null);
            return;
        }
        dto.setAiErrorType(feedback.getErrorType());
        dto.setAiExplanation(feedback.getExplanation());
    }

    private Map<Long, AIFeedback> loadFeedbackBySubmissionIds(List<Long> submissionIds) {
        Map<Long, AIFeedback> feedbackMap = new HashMap<>();
        if (submissionIds.isEmpty()) {
            return feedbackMap;
        }
        for (AIFeedback feedback : aiFeedbackRepository.findBySubmissionIdIn(submissionIds)) {
            feedbackMap.put(feedback.getSubmissionId(), feedback);
        }
        return feedbackMap;
    }

    private String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private Long toLong(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        return Long.parseLong(value.toString());
    }

    private Integer toInteger(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        return Integer.parseInt(value.toString());
    }

    private Double toDouble(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return Double.parseDouble(value.toString());
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
