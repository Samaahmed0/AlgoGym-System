import React, { useEffect, useState, useCallback } from "react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer
} from "recharts";
import { Sparkles, MessageSquare } from "lucide-react";
import { useAdminData } from "../AdminDataContext";
import StatCard from "../components/StatCard";
import "../../styles/admin.css";

const PIE_COLORS = ["#9333ea", "#6366f1", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];

function formatErrorType(type) {
  if (!type) return "—";
  return type.replace(/_/g, " ");
}

export default function AdminAiFeedback() {
  const { getAIFeedbackStats, aiFeedbackVersion } = useAdminData();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    getAIFeedbackStats()
      .then(data => {
        setStats(data);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [getAIFeedbackStats, aiFeedbackVersion]);

  useEffect(() => { load(); }, [load]);

  if (error && !stats) {
    return <div className="admin-error-state">Failed to load AI feedback stats: {error}</div>;
  }

  const errorTypeBreakdown = stats?.errorTypeBreakdown ?? [];
  const problemsNeedingReview = stats?.problemsNeedingReview ?? [];
  const recentFeedback = stats?.recentFeedback ?? [];

  return (
    <div className="admin-ai-feedback-page">
      <h1 className="admin-page-title">AI Feedback</h1>

      <div className="admin-stats-grid admin-stats-grid-2">
        <StatCard
          icon={<Sparkles size={20} />}
          label="Feedback This Week"
          value={stats?.totalFeedbackThisWeek?.toLocaleString() ?? "—"}
          accent="#9333ea"
        />
        <StatCard
          icon={<MessageSquare size={20} />}
          label="Total Feedback (All Time)"
          value={stats?.totalFeedbackAllTime?.toLocaleString() ?? "—"}
          accent="#6366f1"
        />
      </div>

      {error && <div className="admin-error-state" style={{ height: "auto", marginBottom: 16 }}>{error}</div>}

      <div className="admin-charts-grid">
        <div className="admin-chart-card">
          <h3 className="admin-chart-title">Error Type Breakdown</h3>
          <div className="admin-chart-box">
            {errorTypeBreakdown.length === 0 ? (
              <p className="admin-empty-state">No feedback data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={errorTypeBreakdown}
                    dataKey="count"
                    nameKey="errorType"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ errorType, percentage }) =>
                      `${formatErrorType(errorType)} ${percentage}%`
                    }
                    labelLine={false}
                    fontSize={11}
                  >
                    {errorTypeBreakdown.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [value, "Count"]}
                    labelFormatter={(label) => formatErrorType(label)}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
          <table className="admin-data-table">
            <thead>
              <tr>
                <th>Error Type</th>
                <th>Count</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {errorTypeBreakdown.map((row, idx) => (
                <tr key={idx}>
                  <td>
                    <span className="admin-tag-chip-lg">
                      <Sparkles size={12} /> {formatErrorType(row.errorType)}
                    </span>
                  </td>
                  <td>{row.count?.toLocaleString() ?? "—"}</td>
                  <td>{row.percentage != null ? `${row.percentage}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {errorTypeBreakdown.length === 0 && (
            <div className="admin-empty-state">No error types recorded.</div>
          )}
        </div>
      </div>

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`} style={{ marginTop: 20 }}>
        <h3 className="admin-chart-title" style={{ padding: "18px 18px 0" }}>Problems Needing Review</h3>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>Problem ID</th>
              <th>Title</th>
              <th>Help Requests</th>
              <th>Total Submissions</th>
              <th>Help Request Rate</th>
            </tr>
          </thead>
          <tbody>
            {problemsNeedingReview.map(p => (
              <tr key={p.problemId}>
                <td className="admin-cell-mono">{p.problemId}</td>
                <td className="admin-cell-strong">{p.problemTitle}</td>
                <td>{p.helpRequests?.toLocaleString() ?? "—"}</td>
                <td>{p.totalSubmissions?.toLocaleString() ?? "—"}</td>
                <td>{p.helpRequestRate != null ? `${p.helpRequestRate}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {problemsNeedingReview.length === 0 && (
          <div className="admin-empty-state">No problems flagged for review.</div>
        )}
      </div>

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`} style={{ marginTop: 20 }}>
        <h3 className="admin-chart-title" style={{ padding: "18px 18px 0" }}>Recent Feedback</h3>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>Feedback ID</th>
              <th>Submission ID</th>
              <th>User</th>
              <th>Problem ID</th>
              <th>Error Type</th>
              <th>Explanation</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {recentFeedback.map(f => (
              <tr key={f.feedbackId}>
                <td className="admin-cell-mono">{f.feedbackId}</td>
                <td className="admin-cell-mono">{f.submissionId}</td>
                <td className="admin-cell-strong">{f.username}</td>
                <td className="admin-cell-mono">{f.problemId}</td>
                <td>
                  <span className="admin-tag-chip-lg">
                    <Sparkles size={12} /> {formatErrorType(f.errorType)}
                  </span>
                </td>
                <td className="admin-ai-feedback-excerpt">{f.explanation ?? "—"}</td>
                <td>{f.createdAt ? new Date(f.createdAt).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {recentFeedback.length === 0 && (
          <div className="admin-empty-state">No recent feedback.</div>
        )}
      </div>
    </div>
  );
}
