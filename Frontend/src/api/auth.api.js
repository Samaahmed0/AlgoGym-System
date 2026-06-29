const BASE_URL = "http://localhost:8080";

export async function loginUser(username, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) throw new Error("Login failed");
  return response.json();
}

export async function registerUser(data) {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let message = "Registration failed";
    try {
      const errorData = await response.json();
      message = errorData.error || errorData.message || message;
    } catch (_) {}
    throw new Error(message);
  }

  return response.json();
}

export async function forgotPassword(email) {
  const response = await fetch(`${BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    let message = "Something went wrong";
    try {
      const errorData = await response.json();
      message = errorData.message || message;
    } catch (_) {}
    throw new Error(message);
  }

  return response.json();
}

export async function resetPassword(token, newPassword) {
  const response = await fetch(`${BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, newPassword }),
  });

  if (!response.ok) {
    let message = "Reset failed";
    try {
      const errorData = await response.json();
      message = errorData.message || message;
    } catch (_) {}
    throw new Error(message);
  }

  return response.json();
}