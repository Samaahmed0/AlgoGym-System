package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "user_progress")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserProgress {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, unique = true)
    private String userId;

    // Total problems attempted
    @Column(name = "total_submissions")
    private Integer totalSubmissions = 0;

    // Total problems solved (accepted)
    @Column(name = "problems_solved")
    private Integer problemsSolved = 0;

    // By difficulty
    @Column(name = "easy_solved")
    private Integer easySolved = 0;

    @Column(name = "medium_solved")
    private Integer mediumSolved = 0;

    @Column(name = "hard_solved")
    private Integer hardSolved = 0;

    // Acceptance rate
    @Column(name = "acceptance_rate")
    private Double acceptanceRate = 0.0;

    // Current streak (days)
    @Column(name = "current_streak")
    private Integer currentStreak = 0;

    // Longest streak
    @Column(name = "longest_streak")
    private Integer longestStreak = 0;

    // Last submission date
    @Column(name = "last_submission_date")
    private LocalDateTime lastSubmissionDate;

    @Column(name = "algorithm_rating")
    private Integer algorithmRating = 800;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
        // Calculate acceptance rate
        if (totalSubmissions != null && totalSubmissions > 0) {
            acceptanceRate = (problemsSolved * 100.0) / totalSubmissions;
        }
    }
}