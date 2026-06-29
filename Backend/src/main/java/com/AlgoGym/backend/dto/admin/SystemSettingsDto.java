package com.AlgoGym.backend.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SystemSettingsDto {
    private String judge0ApiKeyMasked;
    private String judge0ApiUrl;
    private String groqApiKeyMasked;
    private String groqApiUrl;
    private Boolean maintenanceMode;
    private String appVersion;
}
