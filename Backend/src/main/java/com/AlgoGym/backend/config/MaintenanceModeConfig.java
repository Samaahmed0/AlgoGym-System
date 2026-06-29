package com.AlgoGym.backend.config;

import org.springframework.stereotype.Component;

@Component
public class MaintenanceModeConfig {

    // Singleton @Component — shared by AdminSettingsService, AdminController, and MaintenanceInterceptor.
    // In-memory flag; resets on server restart. Persist via settings table later.
    private boolean maintenanceMode = false;

    public boolean isMaintenanceMode() {
        return maintenanceMode;
    }

    public void setMaintenanceMode(boolean maintenanceMode) {
        this.maintenanceMode = maintenanceMode;
    }
}
