package com.AlgoGym.backend.repository;

import com.AlgoGym.backend.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface NotificationRepository extends JpaRepository<Notification, Long> {

    @Query(value = """
            SELECT * FROM notifications
            WHERE user_id = :userId OR user_id IS NULL
            ORDER BY created_at DESC
            LIMIT 20
            """, nativeQuery = true)
    List<Notification> findNotificationsForUser(@Param("userId") String userId);

    @Query(value = """
            SELECT COUNT(*) FROM notifications
            WHERE (user_id = :userId OR user_id IS NULL)
            AND is_read = false
            """, nativeQuery = true)
    Long countUnreadForUser(@Param("userId") String userId);

    List<Notification> findByUserIdIsNullOrderByCreatedAtDesc();

    @Modifying
    @Query(value = """
            UPDATE notifications
            SET is_read = true
            WHERE user_id = :userId OR user_id IS NULL
            """, nativeQuery = true)
    int markAllAsReadForUser(@Param("userId") String userId);
}
