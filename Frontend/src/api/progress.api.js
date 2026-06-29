const BASE_URL = "http://localhost:8080";

export async function fetchProgress() {
  const token = localStorage.getItem("token");

  const response = await fetch(`${BASE_URL}/progress/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch progress");
  }

  return response.json();
}
