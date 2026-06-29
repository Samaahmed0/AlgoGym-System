import React, { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from "recharts";
import { Trophy, Skull, Users as UsersIcon } from "lucide-react";
import { useAdminData } from "../AdminDataContext";
import "../../styles/admin.css";

const PIE_COLORS = ["#6366f1", "#a855f7", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];
const DAYS_OPTIONS = [7, 30, 90];

export default function AdminAnalytics() {
  const { getAnalytics, getCachedAnalytics } = useAdminData();
  const [days, setDays] = useState(30);
  const [data, setData] = useState(() => getCachedAnalytics(30));
  const [loading, setLoading] = useState(() => !getCachedAnalytics(30));
  const [error, setError] = useState(null);

  useEffect(() => {
    const cached = getCachedAnalytics(days);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    getAnalytics(days)
      .then(next => {
        setData(next);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [days, getAnalytics, getCachedAnalytics]);

  if (loading && !data) {
    return <div className="admin-loading-state"><div className="admin-spinner" /></div>;
  }

  if (error && !data) {
    return <div className="admin-error-state">Failed to load analytics: {error}</div>;
  }

  const { overview, hardest, easiest, mostActive } = data;

  return (
    <div className="admin-analytics-page">
      <div className="admin-page-header-row">
        <h1 className="admin-page-title">Analytics</h1>
        <div className="admin-segmented">
          {DAYS_OPTIONS.map(d => (
            <button
              key={d}
              className={`admin-segmented-btn ${days === d ? "active" : ""}`}
              onClick={() => setDays(d)}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Daily submissions + registrations */}
      <div className="admin-charts-grid">
        <div className="admin-chart-card">
          <h3 className="admin-chart-title">Daily Submissions</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={overview.dailySubmissions ?? []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-chart-card">
          <h3 className="admin-chart-title">New Registrations</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={overview.dailyRegistrations ?? []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#a855f7" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Language distribution + skill levels */}
      <div className="admin-charts-grid">
        <div className="admin-chart-card">
          <h3 className="admin-chart-title">Submissions by Language</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={overview.submissionsByLanguage ?? []}
                  dataKey="submissions"
                  nameKey="language"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ language, percentage }) => `${language} ${percentage}%`}
                  labelLine={false}
                  fontSize={11}
                >
                  {(overview.submissionsByLanguage ?? []).map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-chart-card">
          <h3 className="admin-chart-title">Users by Skill Level</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview.usersBySkillLevel ?? []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top hardest / easiest / most active */}
      <div className="admin-lists-grid">
        <ListCard
          title="Hardest Problems"
          icon={<Skull size={16} color="#ef4444" />}
          items={hardest}
          renderRow={(p) => (
            <>
              <span className="admin-cell-strong">{p.title}</span>
              <span className="admin-list-stat">{p.acceptanceRate}% accepted</span>
            </>
          )}
        />

        <ListCard
          title="Easiest Problems"
          icon={<Trophy size={16} color="#10b981" />}
          items={easiest}
          renderRow={(p) => (
            <>
              <span className="admin-cell-strong">{p.title}</span>
              <span className="admin-list-stat">{p.acceptanceRate}% accepted</span>
            </>
          )}
        />

        <ListCard
          title="Most Active Users"
          icon={<UsersIcon size={16} color="#6366f1" />}
          items={mostActive}
          renderRow={(u) => (
            <>
              <span className="admin-cell-strong">{u.username}</span>
              <span className="admin-list-stat">{u.problemsSolved} solved · {u.currentStreak}🔥</span>
            </>
          )}
        />
      </div>
    </div>
  );
}

function ListCard({ title, icon, items, renderRow }) {
  return (
    <div className="admin-list-card">
      <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {icon} {title}
      </h3>
      <div className="admin-rank-list">
        {(!items || items.length === 0) ? (
          <p className="admin-empty-state">No data yet.</p>
        ) : (
          items.map((item, idx) => (
            <div key={idx} className="admin-rank-row">
              <span className="admin-rank-num">#{idx + 1}</span>
              <div className="admin-rank-content">{renderRow(item)}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}