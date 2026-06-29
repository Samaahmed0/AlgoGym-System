const BASE_URL = "http://localhost:8080";

export async function fetchStudentDashboard(activityPage = 0, activitySize = 50) {
  const token = localStorage.getItem("token");

  const response = await fetch(
    `${BASE_URL}/dashboard/me?activityPage=${activityPage}&activitySize=${activitySize}`,
    {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) throw new Error("Failed to fetch dashboard");

  return response.json();
}

export async function fetchSubmissionSource(submissionId) {
  const token = localStorage.getItem("token");

  const response = await fetch(
    `${BASE_URL}/dashboard/me/submissions/${submissionId}/source`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const msg = response.status === 404 ? "Submission not found" : "Failed to load code";
    throw new Error(msg);
  }

  return response.json();
}