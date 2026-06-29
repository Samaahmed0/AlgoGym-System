package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "ai_feedback")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AIFeedback {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "submission_id", nullable = false)
    private Long submissionId;

    // AI-generated explanation
    @Column(name = "explanation", columnDefinition = "TEXT")
    private String explanation;

    // AI-generated tips
    @Column(name = "tips", columnDefinition = "TEXT")
    private String tips;

    @Column(name = "language_name")
    private String languageName;

    // Error type detected (LOGIC_ERROR, SYNTAX_ERROR, etc.)
    @Column(name = "error_type")
    private String errorType;

    @Column(name = "suggested_approach", columnDefinition = "TEXT")
    private String suggestedApproach;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}