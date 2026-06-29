package com.AlgoGym.backend.dto.notification;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CreateNotificationRequest {
    private String title;
    private String message;
    private String userId;
    private String type = "ANNOUNCEMENT";
}
