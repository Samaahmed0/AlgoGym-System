package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "user_tag_stats")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserTagStats {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "tag", nullable = false)
    private String tag;

    @Column(name = "submissions")
    private Integer submissions = 0;

    @Column(name = "solved")
    private Integer solved = 0;
}