import React, { useEffect, useState, useCallback, useRef } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import {
  Trophy, Target, Activity, Layout, BookOpen, Flame,
  ChevronLeft, ChevronRight, Zap, ChevronDown, ChevronUp, Clock, Cpu, MemoryStick, Code2, X
} from "lucide-react";
import { fetchSubmissionSource } from "../api/studentDashboard.api";
import { useUserData } from "../UserDataContext";
import "../styles/dashboard.css";

function deduplicateActivity(activities) {
  const map = new Map();

  activities.forEach(item => {
    if (!map.has(item.id)) {
      map.set(item.id, { ...item, attempts: 1, allSubmissions: [item] });
    } else {
      const existing = map.get(item.id);
      existing.attempts += 1;
      existing.allSubmissions.push(item);
      if (new Date(item.solvedAt) > new Date(existing.solvedAt)) {
        map.set(item.id, {
          ...item,
          attempts: existing.attempts,
          allSubmissions: existing.allSubmissions,
        });
      }
    }
  });

  return Array.from(map.values());
}

function getRatingTier(rating) {
  const r = Number(rating ?? 0);
  if (r >= 1600) return { tag: "ELITE", color: "#ef4444" };
  if (r >= 1300) return { tag: "ADVANCED", color: "#a855f7" };
  if (r >= 1000) return { tag: "INTERMEDIATE", color: "#f59e0b" };
  return { tag: "BEGINNER", color: "#10b981" };
}

export default function DashboardPage() {
  const { getDashboard, dashboardVersion } = useUserData();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const pageSize = 5;
  const [period, setPeriod] = useState(7);
  const [expandedRow, setExpandedRow] = useState(null);
  const [selectedSubmissions, setSelectedSubmissions] = useState({});
  const [codeModal, setCodeModal] = useState(null);
  const hasLoadedRef = useRef(false);

  const mapDashboardData = useCallback((raw) => {
    const mapped = (raw.recentActivity.activities ?? []).map(item => ({
      id: item.problemId,
      submissionId: item.submissionId,
      title: item.problemTitle,
      topic: item.tag,
      difficulty: item.difficulty,
      solvedAt: item.submittedAt,
      verdict: item.verdict,
      runtime: item.runtime ?? "N/A",
      memory: item.memory ?? "N/A",
      language: item.language ?? "N/A",
      testsPassed: item.testsPassed ?? "N/A",
      totalTests: item.totalTests ?? "N/A",
    }));

    return {
      student: { name: raw.stats.username ?? "Student" },
      stats: {
        solved: raw.stats.totalSolved,
        rank: raw.stats.globalRank,
        rating: raw.stats.algorithmRating,
        streak: raw.stats.currentStreak,
        newlySolvedToday: raw.stats.newlySolvedToday ?? 0,
        velocityMessage: raw.stats.velocityMessage ?? "",
      },
      recentActivity: deduplicateActivity(mapped),
      performanceData: raw.performanceData ?? [],
    };
  }, []);

  const loadDashboard = useCallback(() => {
    const silent = hasLoadedRef.current;
    if (!silent) setLoading(true);

    getDashboard()
      .then(raw => {
        setData(mapDashboardData(raw));
        setError(null);
        hasLoadedRef.current = true;
      })
      .catch(err => {
        console.error("Dashboard fetch failed:", err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [getDashboard, dashboardVersion, mapDashboardData]);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  useEffect(() => {
    if (!codeModal) return undefined;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e) => {
      if (e.key === "Escape") setCodeModal(null);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [codeModal]);

  if (!data && loading) return (
    <div className="loading-screen">
      <div className="loader-ring"></div>
      <p className="loading-text">INITIALIZING_CORE_SYSTEM...</p>
    </div>
  );

  if (error && !data) {
    return (
      <div className="loading-screen">
        <p className="loading-text" style={{ color: "#dc2626" }}>{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const { student, stats, recentActivity, performanceData } = data;

  const totalPages = Math.ceil(recentActivity.length / pageSize);
  const startIndex = (page - 1) * pageSize;
  const visibleActivity = recentActivity.slice(startIndex, startIndex + pageSize);
  const chartData = [...performanceData].slice(-period);

  const ratingTier = getRatingTier(stats?.rating);

  const toggleRow = (id, item) => {
    setExpandedRow(prev => prev === id ? null : id);
    if (!selectedSubmissions[id]) {
      setSelectedSubmissions(prev => ({ ...prev, [id]: item }));
    }
  };

  const selectSubmission = (rowId, sub) => {
    setSelectedSubmissions(prev => ({ ...prev, [rowId]: sub }));
  };

  const openCodeModal = async (sub) => {
    if (sub?.submissionId == null) return;
    setCodeModal({
      loading: true,
      sourceCode: "",
      language: sub.language || "",
      problemTitle: sub.title || "",
      error: null,
    });
    try {
      const result = await fetchSubmissionSource(sub.submissionId);
      setCodeModal({
        loading: false,
        sourceCode: result.sourceCode ?? "",
        language: result.language || sub.language || "",
        problemTitle: result.problemTitle || sub.title || "",
        error: null,
      });
    } catch (err) {
      setCodeModal({
        loading: false,
        sourceCode: "",
        language: sub.language || "",
        problemTitle: sub.title || "",
        error: err.message || "Failed to load code",
      });
    }
  };

  return (
    <div className="dashboard-page-root">
      <div className="mesh-gradient"></div>

      <div className="scroll-container">
        <header className="dash-header">
          <div className="header-left">
            <h1 className="hero-title">
              Welcome back, <span className="text-gradient-vibrant">{student.name.split(' ')[0]}</span> <Zap size={28} className="zap-icon" />
            </h1>
            <p className="hero-subtitle">
              {stats.velocityMessage || "Keep solving to build your velocity trend."}
            </p>
          </div>
          <div className="streak-badge-premium neon-hover">
            <div className="streak-icon-wrap">
              <Flame size={24} className="flame-anim" />
              <span className="streak-num">{stats.streak}</span>
            </div>
            <div className="streak-info">
              <span className="streak-text">DAY STREAK</span>
            </div>
          </div>
        </header>

        <section className="top-stats-row">
          <StatBox
            icon={<Trophy />}
            label="Total Solved"
            value={stats.solved}
            tag={`+${stats.newlySolvedToday} NEW`}
            color="#10b981"
          />
          <StatBox icon={<Target />} label="Global Rank" value={stats.rank} tag="RANKED" color="#3b82f6" />
          <StatBox icon={<Activity />} label="Algorithm Rating" value={stats.rating} tag={ratingTier.tag} color={ratingTier.color} />
        </section>

        <div className="content-grid-main">
          <div className="chart-card-glass neon-hover">
            <div className="card-top">
              <div className="title-with-icon">
                <Layout size={20} className="icon-accent" />
                <h3>Performance Analytics</h3>
              </div>
              <select
                className="period-select-cohesive"
                value={period}
                onChange={e => setPeriod(Number(e.target.value))}
              >
                <option value={7}>LAST 7 DAYS</option>
                <option value={30}>LAST 30 DAYS</option>
              </select>
            </div>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }} dy={15} />
                  <YAxis axisLine={false} tickLine={false} hide />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#3b82f6', strokeWidth: 2 }} />
                  <Area type="monotone" dataKey="xp" stroke="#3b82f6" strokeWidth={4} fill="url(#colorArea)" animationDuration={2000} activeDot={{ r: 6, strokeWidth: 0 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <section className="activity-table-glass neon-hover">
          <div className="card-top">
            <div className="title-with-icon">
              <Activity size={20} className="icon-accent" />
              <h3 className="table-header-title">Recent Activity Logs</h3>
            </div>
            <div className="cohesive-nav-group">
              <button className="nav-btn" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft size={18} />
              </button>
              <span className="nav-page-indicator">{page} / {totalPages || 1}</span>
              <button className="nav-btn" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || totalPages === 0}>
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          <div className="table-body">
            {visibleActivity.length === 0 ? (
              <p className="empty-state">No activity yet. Solve your first problem!</p>
            ) : (
              visibleActivity.map(item => {
                const selected = selectedSubmissions[item.id] ?? item;
                const isExpanded = expandedRow === item.id;

                return (
                  <div key={item.id} className="activity-entry">
                    <div
                      className={`activity-row-modern blue-hover-state ${isExpanded ? "row-expanded" : ""}`}
                      onClick={() => toggleRow(item.id, item)}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="activity-left">
                        <div className="activity-icon-box academic-blue">
                          <BookOpen size={18} />
                        </div>
                        <div className="activity-info">
                          <span className="activity-topic-tag">{item.topic}</span>
                          <strong className="activity-title-text">{item.title}</strong>
                        </div>
                      </div>

                      <div className="activity-right">
                        {item.attempts >= 1 && (
                          <span className="attempts-badge">{item.attempts} attempts</span>
                        )}
                        <div className={`activity-status-badge ${item.difficulty.toLowerCase()}`}>
                          {item.difficulty}
                        </div>
                        <span className="activity-date-text">
                          {new Date(item.solvedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </span>
                        {isExpanded
                          ? <ChevronUp size={16} className="expand-icon" />
                          : <ChevronDown size={16} className="expand-icon" />
                        }
                      </div>
                    </div>

                    {isExpanded && (
                      <div
                        className="activity-detail-panel"
                        title="Double-click to view submitted code"
                        onDoubleClick={(e) => {
                          e.stopPropagation();
                          openCodeModal(selected);
                        }}
                      >
                        <div className="detail-grid">
                          <div className="detail-item">
                            <Clock size={14} className="detail-icon" />
                            <span className="detail-label">Runtime</span>
                            <span className="detail-value">{selected.runtime}</span>
                          </div>

                          <div className="detail-item">
                            <MemoryStick size={14} className="detail-icon" />
                            <span className="detail-label">Memory</span>
                            <span className="detail-value">{selected.memory}</span>
                          </div>

                          <div className="detail-item">
                            <Code2 size={14} className="detail-icon" />
                            <span className="detail-label">Language</span>
                            <span className="detail-value">{selected.language}</span>
                          </div>

                          <div className="detail-item">
                            <Cpu size={14} className="detail-icon" />
                            <span className="detail-label">Tests Passed</span>
                            <span className="detail-value">{selected.testsPassed} / {selected.totalTests}</span>
                          </div>

                          <div className="detail-item">
                            <Activity size={14} className="detail-icon" />
                            <span className="detail-label">Verdict</span>
                            <span className={`detail-verdict ${selected.verdict?.toLowerCase().replace(' ', '-')}`}>
                              {selected.verdict}
                            </span>
                          </div>

                          <div className="detail-item">
                            <Clock size={14} className="detail-icon" />
                            <span className="detail-label">Submitted</span>
                            <span className="detail-value">
                              {new Date(selected.solvedAt).toLocaleString('en-US', {
                                month: 'short', day: 'numeric',
                                hour: '2-digit', minute: '2-digit'
                              })}
                            </span>
                          </div>
                        </div>

                        {item.attempts >= 1 && (
                          <div className="submissions-history">
                            <p className="submissions-history-title">All Submissions — click to select, double-click for code</p>
                            {item.allSubmissions.map((sub, idx) => {
                              const isSelected = selected.solvedAt === sub.solvedAt;
                              return (
                                <div
                                  key={idx}
                                  className={`submission-history-row ${isSelected ? "submission-selected" : ""}`}
                                  onClick={() => selectSubmission(item.id, sub)}
                                  onDoubleClick={(e) => {
                                    e.stopPropagation();
                                    selectSubmission(item.id, sub);
                                    openCodeModal(sub);
                                  }}
                                  style={{ cursor: "pointer" }}
                                  title="Double-click to view this attempt's code"
                                >
                                  <span className="sub-num">#{idx + 1}</span>
                                  <span className={`detail-verdict ${sub.verdict?.toLowerCase().replace(' ', '-')}`}>
                                    {sub.verdict}
                                  </span>
                                  <span className="detail-value">{sub.language}</span>
                                  <span className="detail-value">
                                    {new Date(sub.solvedAt).toLocaleString('en-US', {
                                      month: 'short', day: 'numeric',
                                      hour: '2-digit', minute: '2-digit'
                                    })}
                                  </span>
                                  {isSelected && (
                                    <span className="selected-indicator">● viewing</span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>

      {/* Code Viewer Modal */}
      {codeModal && (
        <div className="code-modal-backdrop" onClick={() => setCodeModal(null)}>
          <div className="code-modal-card" onClick={e => e.stopPropagation()}>
            <div className="code-modal-header">
              <div>
                <h2 className="code-modal-title">{codeModal.problemTitle || "Submission"}</h2>
                {codeModal.language && <p className="code-modal-meta">{codeModal.language}</p>}
              </div>
              <button className="code-modal-close" onClick={() => setCodeModal(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="code-modal-body">
              {codeModal.loading && <p className="code-modal-status">Loading source…</p>}
              {codeModal.error && <p className="code-modal-error">{codeModal.error}</p>}
              {!codeModal.loading && !codeModal.error && (
                <pre className="code-modal-pre"><code>{codeModal.sourceCode}</code></pre>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload?.length) {
    return (
      <div className="custom-tooltip-premium">
        <p className="val">{payload[0].value} XP</p>
        <p>{payload[0].payload.submissionCount} submissions</p>
      </div>
    );
  }
  return null;
};

function StatBox({ icon, label, value, tag, color }) {
  return (
    <div className="stat-card-premium neon-hover" style={{ "--neon-color": color }}>
      <div className="stat-icon-circle-glass" style={{ color: color }}>{icon}</div>
      <div className="stat-main">
        <span className="stat-label-dim">{label}</span>
        <div className="stat-val-group">
          <span className="stat-value-bold">{value}</span>
          <span className="stat-tag-pill" style={{ background: `${color}15`, color: color }}>{tag}</span>
        </div>
      </div>
    </div>
  );
}