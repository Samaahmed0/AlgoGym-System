const BASE_URL = "http://localhost:8080";

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export async function adminFetch(path, options = {}) {
  const token = localStorage.getItem("token");

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  // Global status handling
  if (response.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }

  if (response.status === 403) {
    window.location.href = "/dashboard";
    throw new ApiError(403, "Not authorized");
  }

  if (response.status === 503) {
    throw new ApiError(503, "Platform under maintenance");
  }

  if (!response.ok) {
    let message = "Something went wrong";
    try {
      const errBody = await response.json();
      message = errBody.message || errBody.error || message;
    } catch (_) {}
    throw new ApiError(response.status, message);
  }

  // DELETE/PUT endpoints sometimes return plain text or empty body
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch (_) {
    return text;
  }
}

export async function fetchCurrentUserRole() {
  return adminFetch("/auth/me");
}
export async function fetchAdminStats() {
  return adminFetch("/admin/stats");
}

export async function fetchAdminHealth() {
  return adminFetch("/admin/health");
}
// ── Users ──
export async function fetchAdminUsers(page = 0, size = 10, search = "") {
  const params = new URLSearchParams({ page, size });
  if (search) params.append("search", search);
  return adminFetch(`/admin/users?${params.toString()}`);
}

export async function updateUserRole(userId, role) {
  return adminFetch(`/admin/users/${userId}/role`, {
    method: "PUT",
    body: JSON.stringify({ role }),
  });
}

export async function deleteAdminUser(userId) {
  return adminFetch(`/admin/users/${userId}`, { method: "DELETE" });
}

export async function fetchRoleChangeLog() {
  return adminFetch("/admin/users/role-change-log");
}

// ── Problems ──
export async function fetchAdminProblems(page = 0, size = 20, search = "", difficulty = "", visible = "all") {
  const params = new URLSearchParams({ page, size, visible });
  if (search) params.append("search", search);
  if (difficulty) params.append("difficulty", difficulty);
  return adminFetch(`/admin/problems?${params.toString()}`);
}

export async function toggleProblemVisibility(problemId, visible) {
  const params = new URLSearchParams({ id: problemId });
  return adminFetch(`/admin/problems/visibility?${params.toString()}`, {
    method: "PUT",
    body: JSON.stringify({ visible }),
  });
}

export async function deleteAdminProblem(problemId) {
  const params = new URLSearchParams({ id: problemId });
  return adminFetch(`/admin/problems?${params.toString()}`, { method: "DELETE" });
}

export async function bulkImportProblems(file, format = "json") {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`http://localhost:8080/admin/problems/bulk-import?format=${format}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }, // no Content-Type — browser sets multipart boundary
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Bulk import failed");
  }

  return response.json();
}
export async function fetchAdminSubmissions(page = 0, size = 20, filters = {}) {
  const params = new URLSearchParams({ page, size });
  if (filters.verdict) params.append("verdict", filters.verdict);
  if (filters.language) params.append("language", filters.language);
  if (filters.userId) params.append("userId", filters.userId);
  if (filters.problemId) params.append("problemId", filters.problemId);
  return adminFetch(`/admin/submissions?${params.toString()}`);
}

export async function fetchAdminSubmissionDetail(id) {
  return adminFetch(`/admin/submissions/${id}`);
}

export async function fetchAnalyticsOverview(days = 30) {
  return adminFetch(`/admin/analytics/overview?days=${days}`);
}

export async function fetchTopHardestProblems(limit = 10) {
  return adminFetch(`/admin/analytics/problems/top-hardest?limit=${limit}`);
}

export async function fetchTopEasiestProblems(limit = 10) {
  return adminFetch(`/admin/analytics/problems/top-easiest?limit=${limit}`);
}

export async function fetchMostActiveUsers(limit = 10) {
  return adminFetch(`/admin/analytics/users/most-active?limit=${limit}`);
}
export async function fetchAllTags() {
  return adminFetch("/admin/tags");
}

export async function fetchMostAttemptedTags() {
  return adminFetch("/admin/tags/most-attempted");
}

export async function renameTag(oldTag, newTag) {
  return adminFetch("/admin/tags/rename", {
    method: "PUT",
    body: JSON.stringify({ oldTag, newTag }),
  });
}

// ── AI Feedback ──
export async function fetchAIFeedbackStats() {
  return adminFetch("/admin/ai-feedback/stats");
}

// ── Notifications ──
export async function fetchBroadcastNotifications() {
  return adminFetch("/admin/notifications/broadcasts");
}

export async function createAdminNotification(body) {
  return adminFetch("/admin/notifications", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ── Settings ──
export async function fetchAdminSettings() {
  return adminFetch("/admin/settings");
}

export async function updateMaintenanceMode(enabled) {
  return adminFetch("/admin/settings/maintenance", {
    method: "PUT",
    body: JSON.stringify({ enabled }),
  });
}