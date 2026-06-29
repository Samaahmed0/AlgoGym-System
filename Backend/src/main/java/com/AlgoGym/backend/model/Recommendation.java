package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "recommendations")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Recommendation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    // Recommended problem
    @Column(name = "problem_id", nullable = false)
    private String problemId;

    @Column(name = "reason", columnDefinition = "TEXT")
    private String reason;

    // Confidence score (0-100)
    @Column(name = "confidence_score")
    private Double confidenceScore;

    // Has user attempted this problem after recommendation?
    @Column(name = "is_attempted")
    private Boolean isAttempted = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}