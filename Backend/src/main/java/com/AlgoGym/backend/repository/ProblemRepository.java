package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.Problem;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ProblemRepository extends JpaRepository<Problem, String> {

    @Query(value = "SELECT COUNT(*) FROM \"Problems\" WHERE rating >= 0 AND rating <= 1199", nativeQuery = true)
    Long countEasyProblems();

    @Query(value = "SELECT COUNT(*) FROM \"Problems\" WHERE rating >= 1200 AND rating <= 1599", nativeQuery = true)
    Long countMediumProblems();

    @Query(value = "SELECT COUNT(*) FROM \"Problems\" WHERE rating >= 1600", nativeQuery = true)
    Long countHardProblems();

    @Query(value = """
            SELECT COUNT(*) FROM "Problems"
            WHERE rating < 1200 AND is_visible = true
            """, nativeQuery = true)
    Long countVisibleEasyProblems();

    @Query(value = """
            SELECT COUNT(*) FROM "Problems"
            WHERE rating >= 1200 AND rating <= 1599 AND is_visible = true
            """, nativeQuery = true)
    Long countVisibleMediumProblems();

    @Query(value = """
            SELECT COUNT(*) FROM "Problems"
            WHERE rating >= 1600 AND is_visible = true
            """, nativeQuery = true)
    Long countVisibleHardProblems();

    @Query(value = """
            SELECT tag, COUNT(*) as problem_count
            FROM "Problems",
            jsonb_array_elements_text(tags) AS tag
            GROUP BY tag
            ORDER BY problem_count DESC
            """, nativeQuery = true)
    List<Object[]> findAllTagsWithCount();

    @Modifying
    @Query(value = """
            UPDATE "Problems"
            SET tags = (
              SELECT COALESCE(jsonb_agg(
                CASE WHEN elem = to_jsonb(:oldTag) THEN to_jsonb(:newTag)
                     ELSE elem END
              ), '[]'::jsonb)
              FROM jsonb_array_elements(tags) AS elem
            )
            WHERE tags @> jsonb_build_array(:oldTag)
            """, nativeQuery = true)
    int renameTagInProblems(@Param("oldTag") String oldTag, @Param("newTag") String newTag);
}