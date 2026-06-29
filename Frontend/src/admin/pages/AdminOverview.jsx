import React, { useEffect, useState, useCallback } from "react";
import {
  Users, FileCode2, ListChecks, TrendingUp, Activity, Percent
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";
import { useAdminData } from "../AdminDataContext";
import StatCard from "../components/StatCard";
import HealthBadge from "../components/HealthBadge";
import "../../styles/admin.css";

const REFRESH_POLL_MS = 30000;

export default function AdminOverview() {
  const {
    overviewStats,
    overviewHealth,
    getOverviewStats,
    getOverviewHealth,
    refreshOverviewStats,
    refreshOverviewHealth,
  } = useAdminData();

  const [stats, setStats] = useState(overviewStats);
  const [health, setHealth] = useState(overviewHealth);
  const [loading, setLoading] = useState(!overviewStats);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    const needsInitialLoad = !overviewStats;
    if (needsInitialLoad) setLoading(true);

    return Promise.all([getOverviewStats(), getOverviewHealth()])
      .then(([statsData, healthData]) => {
        setStats(statsData);
        setHealth(healthData);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => {
        if (needsInitialLoad) setLoading(false);
      });
  }, [getOverviewStats, getOverviewHealth, overviewStats]);

  useEffect(() => {
    if (overviewStats) {
      setStats(overviewStats);
      setHealth(overviewHealth);
      setLoading(false);
      return;
    }
    load();
  }, [overviewStats, overviewHealth, load]);

  // Background refresh only while overview is open
  useEffect(() => {
    const interval = setInterval(() => {
      Promise.all([refreshOverviewStats(), refreshOverviewHealth()])
        .then(([statsData, healthData]) => {
          setStats(statsData);
          setHealth(healthData);
        })
        .catch(err => console.error("Overview refresh failed:", err));
    }, REFRESH_POLL_MS);
    return () => clearInterval(interval);
  }, [refreshOverviewStats, refreshOverviewHealth]);

  if (loading && !stats) {
    return (
      <div className="admin-loading-state">
        <div className="admin-spinner" />
      </div>
    );
  }

  if (error && !stats) {
    return <div className="admin-error-state">Failed to load overview: {error}</div>;
  }

  return (
    <div className="admin-overview">
      <h1 className="admin-page-title">Overview</h1>

      <div className="admin-stats-grid">
        <StatCard icon={<Users size={20} />} label="Total Users" value={stats.totalUsers?.toLocaleString() ?? "—"} accent="#6366f1" />
        <StatCard icon={<FileCode2 size={20} />} label="Total Problems" value={stats.totalProblems?.toLocaleString() ?? "—"} accent="#a855f7" />
        <StatCard icon={<ListChecks size={20} />} label="Total Submissions" value={stats.totalSubmissions?.toLocaleString() ?? "—"} accent="#3b82f6" />
        <StatCard icon={<TrendingUp size={20} />} label="Submissions Today" value={stats.submissionsToday?.toLocaleString() ?? "—"} accent="#10b981" />
        <StatCard icon={<Activity size={20} />} label="Active Users (7d)" value={stats.activeUsersThisWeek?.toLocaleString() ?? "—"} accent="#f59e0b" />
        <StatCard icon={<Percent size={20} />} label="Acceptance Rate" value={`${stats.overallAcceptanceRate ?? 0}%`} accent="#ef4444" />
      </div>

      <div className="admin-charts-grid">
        <div className="admin-chart-card">
          <h3 className="admin-chart-title">Daily Submissions (30 days)</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.dailySubmissions ?? []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="subGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2.5} fill="url(#subGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-chart-card">
          <h3 className="admin-chart-title">New Registrations (30 days)</h3>
          <div className="admin-chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.dailyRegistrations ?? []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#a855f7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="admin-health-card">
        <h3 className="admin-chart-title">System Health</h3>
        {health ? (
          <div className="health-list">
            <HealthBadge name="Database" status={health.databaseStatus} latencyMs={health.databaseLatencyMs} />
            <HealthBadge name="Judge0 API" status={health.judge0Status} latencyMs={health.judge0LatencyMs} />
            <HealthBadge name="Groq API" status={health.groqStatus} latencyMs={health.groqLatencyMs} />
          </div>
        ) : (
          <p className="admin-page-placeholder">Checking system health...</p>
        )}
        {health?.checkedAt && (
          <p className="health-checked-at">
            Last checked: {new Date(health.checkedAt).toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
}
