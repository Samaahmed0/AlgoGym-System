const API_BASE = "http://localhost:8080/api";

export async function fetchProblems({
  page = 0,
  size = 10,
  title = "",
  difficulty = [],
  topic = [],
  status = [],
} = {}) {
  const params = new URLSearchParams({ page, size });
  if (title) params.append("title", title);
  difficulty.forEach(d => params.append("difficulty", d));
  topic.forEach(t => params.append("tags", t));
  status.forEach(s => params.append("status", s));

  const token = localStorage.getItem("token");
  const response = await fetch(`${API_BASE}/problems?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) throw new Error("Failed to load problems");
  return response.json();
}

export async function fetchProblemTags() {
  const token = localStorage.getItem("token");
  const response = await fetch(`${API_BASE}/problems/tags`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) throw new Error("Failed to load problem tags");
  return response.json();
}
