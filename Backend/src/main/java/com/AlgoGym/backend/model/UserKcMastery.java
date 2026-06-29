package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(
        name = "user_kc_mastery",
        uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "kc_name"})
)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserKcMastery {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "kc_name", nullable = false)
    private String kcName;

    @Column(name = "mastery", nullable = false)
    private Double mastery;

    @Column(name = "n_attempts")
    private Integer nAttempts = 0;

    @Column(name = "is_weak")
    private Boolean isWeak = false;

    @Column(name = "rank")
    private Integer rank;
}
