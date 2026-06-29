const BASE_URL = "http://localhost:8080";

export async function fetchCurrentUser() {
  const token = localStorage.getItem("token");

  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) throw new Error("Failed to fetch user");

  return response.json();
}

export async function updateUser(id, userData) {
  const token = localStorage.getItem("token");

  const response = await fetch(`${BASE_URL}/users/${id}`, {
    method: "PUT",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    let message = "Failed to update user";
    try {
      const body = await response.json();
      message = body.error || body.message || message;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(message);
  }

  return response.json();
}