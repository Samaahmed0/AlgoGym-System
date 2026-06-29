package com.AlgoGym.backend.service;

import com.AlgoGym.backend.model.Problem;
import com.AlgoGym.backend.model.Submission;
import com.AlgoGym.backend.model.UserProgress;
import com.AlgoGym.backend.model.UserTagStats;
import com.AlgoGym.backend.repository.ProblemRepository;
import com.AlgoGym.backend.repository.SubmissionRepository;
import com.AlgoGym.backend.repository.UserProgressRepository;
import com.AlgoGym.backend.repository.UserTagStatsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class UserProgressService {

    private final UserProgressRepository userProgressRepository;
    private final UserTagStatsRepository userTagStatsRepository;
    private final ProblemRepository problemRepository;
    private final SubmissionRepository submissionRepository;

    @Transactional
    public void initializeProgress(String userId) {
        if (userProgressRepository.findByUserId(userId).isPresent()) return;

        UserProgress progress = new UserProgress();
        progress.setUserId(userId);
        progress.setTotalSubmissions(0);
        progress.setProblemsSolved(0);
        progress.setEasySolved(0);
        progress.setMediumSolved(0);
        progress.setHardSolved(0);
        progress.setAcceptanceRate(0.0);
        progress.setCurrentStreak(0);
        progress.setLongestStreak(0);
        progress.setAlgorithmRating(800);

        userProgressRepository.save(progress);
    }

    @Transactional
    public void updateProgress(Submission submission) {
        String userId = submission.getUserId();

        UserProgress progress = userProgressRepository.findByUserId(userId)
                .orElseGet(() -> {
                    initializeProgress(userId);
                    return userProgressRepository.findByUserId(userId).orElseThrow();
                });

        // Fetch problem once — used for difficulty, rating, and tags
        Problem problem = problemRepository.findById(submission.getProblemId()).orElse(null);

        // Always increment total submissions
        progress.setTotalSubmissions(progress.getTotalSubmissions() + 1);

        boolean isFirstAcceptance = false;

        if ("ACCEPTED".equals(submission.getVerdict())) {
            // submission is already saved, so count=1 means this is the first
            Long acceptedCount = submissionRepository.countAcceptedSubmissions(
                    userId, submission.getProblemId()
            );
            isFirstAcceptance = acceptedCount <= 1;

            if (isFirstAcceptance) {
                progress.setProblemsSolved(progress.getProblemsSolved() + 1);

                String difficulty = getDifficulty(problem);
                switch (difficulty) {
                    case "EASY"   -> progress.setEasySolved(progress.getEasySolved() + 1);
                    case "MEDIUM" -> progress.setMediumSolved(progress.getMediumSolved() + 1);
                    case "HARD"   -> progress.setHardSolved(progress.getHardSolved() + 1);
                }
            }

            // Robust streak: base it on the previous ACCEPTED submission date from the DB,
            // not on whatever is currently stored in user_progress (which may have been polluted before).
            LocalDateTime previousAcceptedAt = submissionRepository.findPreviousAcceptedAt(
                    userId, submission.getSubmittedAt()
            );
            updateStreak(progress, previousAcceptedAt, submission.getSubmittedAt());
            progress.setLastSubmissionDate(submission.getSubmittedAt());
        }

        // Acceptance rate
        if (progress.getTotalSubmissions() > 0) {
            progress.setAcceptanceRate(
                    (progress.getProblemsSolved() * 100.0) / progress.getTotalSubmissions()
            );
        }

        // Algorithm rating — recalculate every submission
        progress.setAlgorithmRating(calculateAlgorithmRating(progress));

        // Tag stats — update for every submission
        updateTagStats(userId, submission, problem, isFirstAcceptance);

        userProgressRepository.save(progress);
    }

    // ── Algorithm Rating ──────────────────────────────────────────────────────
    // Uses actual problem ratings rather than flat difficulty buckets.
    // Base 800 + weighted contribution from each tier + streak bonus + accuracy bonus
    private Integer calculateAlgorithmRating(UserProgress progress) {
        int easy   = progress.getEasySolved()   != null ? progress.getEasySolved()   : 0;
        int medium = progress.getMediumSolved()  != null ? progress.getMediumSolved() : 0;
        int hard   = progress.getHardSolved()    != null ? progress.getHardSolved()   : 0;
        int streak = progress.getCurrentStreak() != null ? progress.getCurrentStreak(): 0;
        double acceptanceRate = progress.getAcceptanceRate() != null ? progress.getAcceptanceRate() : 0.0;

        // Weighted points per difficulty using midpoint of each rating band
        // Easy  avg ~1000, Medium avg ~1400, Hard avg ~1800
        double easyPoints   = easy   * 1000 * 0.08;
        double mediumPoints = medium * 1400 * 0.10;
        double hardPoints   = hard   * 1800 * 0.14;

        // Streak bonus: +2 per day, capped at 100
        double streakBonus = Math.min(streak * 2, 100);

        // Accuracy bonus: up to +150 for 100% acceptance rate
        double accuracyBonus = acceptanceRate * 1.5;

        return (int) Math.round(800 + easyPoints + mediumPoints + hardPoints + streakBonus + accuracyBonus);
    }

    // ── Tag Stats ─────────────────────────────────────────────────────────────
    private void updateTagStats(String userId, Submission submission, Problem problem, boolean isFirstAcceptance) {
        if (problem == null || problem.getTags() == null || problem.getTags().isEmpty()) return;

        boolean isAccepted = "ACCEPTED".equals(submission.getVerdict());

        for (String tag : problem.getTags()) {
            UserTagStats tagStat = userTagStatsRepository
                    .findByUserIdAndTag(userId, tag)
                    .orElseGet(() -> {
                        UserTagStats newStat = new UserTagStats();
                        newStat.setUserId(userId);
                        newStat.setTag(tag);
                        newStat.setSubmissions(0);
                        newStat.setSolved(0);
                        return newStat;
                    });

            // Every submission increments tag submission count
            tagStat.setSubmissions(tagStat.getSubmissions() + 1);

            // Only first acceptance increments solved count
            if (isAccepted && isFirstAcceptance) {
                tagStat.setSolved(tagStat.getSolved() + 1);
            }

            userTagStatsRepository.save(tagStat);
        }
    }

    // ── Difficulty ────────────────────────────────────────────────────────────
    private String getDifficulty(Problem problem) {
        if (problem == null || problem.getRating() == null) return "MEDIUM";
        long rating = problem.getRating();
        if (rating < 1200) return "EASY";
        if (rating < 1600) return "MEDIUM";
        return "HARD";
    }

    // ── Streak ────────────────────────────────────────────────────────────────
    private void updateStreak(UserProgress progress, LocalDateTime previousAcceptedAt, LocalDateTime submissionTime) {
        LocalDate today = submissionTime.toLocalDate();
        LocalDate lastDate = previousAcceptedAt != null ? previousAcceptedAt.toLocalDate() : null;

        if (lastDate == null) {
            progress.setCurrentStreak(1);
            progress.setLongestStreak(1);
        }  else if (lastDate.equals(today)) {
            // Same day — only set to 1 if streak is still 0
            if (progress.getCurrentStreak() == 0) {
                progress.setCurrentStreak(1);
                progress.setLongestStreak(1);
            }
        } else if (lastDate.equals(today.minusDays(1))) {
            int newStreak = progress.getCurrentStreak() + 1;
            progress.setCurrentStreak(newStreak);
            if (newStreak > progress.getLongestStreak()) {
                progress.setLongestStreak(newStreak);
            }
        } else {
            progress.setCurrentStreak(1);
        }
    }
}