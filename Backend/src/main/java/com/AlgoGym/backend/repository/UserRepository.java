package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, String> {
    Optional<User> findByUsername(String username);
    Optional<User> findByEmail(String email);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);

    Page<User> findByUsernameContainingIgnoreCaseOrEmailContainingIgnoreCase(
            String username, String email, Pageable pageable);

    @Query("SELECT u.skillLevel, COUNT(u) FROM User u GROUP BY u.skillLevel")
    List<Object[]> countBySkillLevel();

    @Query(value = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users
            WHERE created_at >= :since
            GROUP BY DATE(created_at)
            ORDER BY date ASC
            """, nativeQuery = true)
    List<Object[]> findDailyRegistrationCounts(@Param("since") LocalDateTime since);
}