package com.AlgoGym.backend.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.util.List;

@Entity

@Table(name = "\"Problems\"", schema = "public")

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Problem {

    @Id
    @Column(name = "id", nullable = false, unique = true)
    private String id;

    @Column(name = "contest_id")
    private Long contestId;

    @Column(name = "contest_start_year")
    private Long contestStartYear;

    @Column(name = "index")
    private String problemIndex;

    @Column(name = "time_limit")
    private Double timeLimit;

    @Column(name = "memory_limit")
    private Long memoryLimit;

    @Column(name = "title", columnDefinition = "TEXT")
    private String title;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "input_format", columnDefinition = "TEXT")
    private String inputFormat;

    @Column(name = "output_format", columnDefinition = "TEXT")
    private String outputFormat;

    @Column(name = "note", columnDefinition = "TEXT")
    private String note;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "examples", columnDefinition = "jsonb")
    private List<TestCase> examples;

    @Column(name = "editorial", columnDefinition = "TEXT")
    private String editorial;

    @Column(name = "rating")
    private Long rating;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "tags", columnDefinition = "jsonb")
    private List<String> tags;

    @Column(name = "testset_size")
    private Long testsetSize;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "official_tests", columnDefinition = "jsonb")
    private List<TestCase> officialTests;

    // Add this field to Problem.java with the others:
    @Column(name = "difficulty", columnDefinition = "TEXT")
    private String difficulty;

    // DB default: ALTER TABLE "Problems" ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT true;
    @Column(name = "is_visible")
    private Boolean isVisible;
}