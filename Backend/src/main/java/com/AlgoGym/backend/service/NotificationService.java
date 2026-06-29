package com.AlgoGym.backend.service;

import com.AlgoGym.backend.dto.notification.CreateNotificationRequest;
import com.AlgoGym.backend.dto.notification.NotificationDto;
import com.AlgoGym.backend.model.Notification;
import com.AlgoGym.backend.repository.NotificationRepository;
import com.AlgoGym.backend.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;

    public List<NotificationDto> getNotificationsForUser(String userId) {
        return notificationRepository.findNotificationsForUser(userId).stream()
                .map(this::toDto)
                .toList();
    }

    public long getUnreadCount(String userId) {
        Long count = notificationRepository.countUnreadForUser(userId);
        return count != null ? count : 0L;
    }

    public NotificationDto markAsRead(Long id, String userId) {
        Notification notification = notificationRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Notification not found"));

        if (notification.getUserId() != null && !notification.getUserId().equals(userId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Notification does not belong to user");
        }

        notification.setIsRead(true);
        return toDto(notificationRepository.save(notification));
    }

    @Transactional
    public void markAllAsRead(String userId) {
        notificationRepository.markAllAsReadForUser(userId);
    }

    public NotificationDto createNotification(CreateNotificationRequest request) {
        if (request.getTitle() == null || request.getTitle().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "title is required");
        }
        if (request.getMessage() == null || request.getMessage().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "message is required");
        }

        if (request.getUserId() != null && !request.getUserId().isBlank()) {
            userRepository.findById(request.getUserId())
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "User not found"));
        }

        Notification notification = new Notification();
        notification.setUserId(blankToNull(request.getUserId()));
        notification.setTitle(request.getTitle());
        notification.setMessage(request.getMessage());
        notification.setType(
                request.getType() == null || request.getType().isBlank()
                        ? "ANNOUNCEMENT"
                        : request.getType()
        );

        return toDto(notificationRepository.save(notification));
    }

    public List<NotificationDto> getBroadcasts() {
        return notificationRepository.findByUserIdIsNullOrderByCreatedAtDesc().stream()
                .map(this::toDto)
                .toList();
    }

    private NotificationDto toDto(Notification notification) {
        return new NotificationDto(
                notification.getId(),
                notification.getTitle(),
                notification.getMessage(),
                notification.getType(),
                notification.getIsRead(),
                notification.getCreatedAt()
        );
    }

    private String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }
}
