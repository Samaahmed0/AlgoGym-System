package com.AlgoGym.backend.service;

import com.AlgoGym.backend.config.MaintenanceModeConfig;
import com.AlgoGym.backend.dto.admin.SystemSettingsDto;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AdminSettingsService {

    private static final String APP_VERSION = "1.0.0";

    private final MaintenanceModeConfig maintenanceModeConfig;

    @Value("${judge0.api.key}")
    private String judge0ApiKey;

    @Value("${judge0.api.url}")
    private String judge0ApiUrl;

    @Value("${groq.api.key}")
    private String groqApiKey;

    @Value("${groq.api.url}")
    private String groqApiUrl;

    public SystemSettingsDto getSettings() {
        return new SystemSettingsDto(
                maskKey(judge0ApiKey),
                judge0ApiUrl,
                maskKey(groqApiKey),
                groqApiUrl,
                maintenanceModeConfig.isMaintenanceMode(),
                APP_VERSION
        );
    }

    public void setMaintenanceMode(boolean enabled) {
        maintenanceModeConfig.setMaintenanceMode(enabled);
    }

    public static String maskKey(String key) {
        if (key == null || key.length() < 4) {
            return "••••••••••••????";
        }
        return "••••••••••••" + key.substring(key.length() - 4);
    }
}
