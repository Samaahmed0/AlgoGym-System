package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "user_weakness_summary")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserWeaknessSummary {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, unique = true)
    private String userId;

    @Column(name = "weak_kcs", columnDefinition = "TEXT")
    private String weakKcs;

    @Column(name = "n_weak")
    private Integer nWeak = 0;

    @Column(name = "weakest_5", columnDefinition = "TEXT", nullable = false)
    private String weakest5;

    @Column(name = "related_kcs", columnDefinition = "TEXT")
    private String relatedKcs;
}
