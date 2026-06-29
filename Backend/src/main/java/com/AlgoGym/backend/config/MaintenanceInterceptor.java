package com.AlgoGym.backend.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
@RequiredArgsConstructor
public class MaintenanceInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(MaintenanceInterceptor.class);

    private final MaintenanceModeConfig maintenanceModeConfig;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        String path = request.getRequestURI();
        // TEMPORARY: remove after confirming maintenance mode is not stuck enabled
        log.info("Maintenance check: enabled={}, path={}", maintenanceModeConfig.isMaintenanceMode(), path);

        if (!maintenanceModeConfig.isMaintenanceMode()) {
            return true;
        }

        if (path.startsWith("/admin") || path.startsWith("/auth")) {
            return true;
        }

        response.setStatus(HttpServletResponse.SC_SERVICE_UNAVAILABLE);
        response.setContentType("application/json");
        response.getWriter().write(
                "{\"message\":\"Platform is under maintenance. Please check back soon.\"}"
        );
        return false;
    }
}
