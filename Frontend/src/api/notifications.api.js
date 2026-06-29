const BASE_URL = "http://localhost:8080";

async function notificationFetch(path, options = {}) {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("Not authenticated");

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = "Something went wrong";
    try {
      const errBody = await response.json();
      message = errBody.message || errBody.error || message;
    } catch (_) {}
    throw new Error(message);
  }

  const text = await response.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch (_) {
    return text;
  }
}

export async function fetchNotifications() {
  return notificationFetch("/notifications");
}

export async function fetchUnreadCount() {
  return notificationFetch("/notifications/unread-count");
}

export async function markNotificationRead(id) {
  return notificationFetch(`/notifications/${id}/read`, { method: "PUT" });
}

export async function markAllNotificationsRead() {
  return notificationFetch("/notifications/read-all", { method: "PUT" });
}
