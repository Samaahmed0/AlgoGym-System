import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    ResponsiveContainer,
} from "recharts";
import { Activity, Flame, Target } from "lucide-react";
import "../styles/ProgressPage.css";
import { useUserData } from "../UserDataContext";

const ProgressPage = () => {
    const { getProgress, progressVersion } = useUserData();
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(() => {
        setLoading(true);
        getProgress()
            .then((data) => {
                setProgress(data);
                setError(null);
            })
            .catch((err) => {
                setError(err.message || "Failed to load progress");
            })
            .finally(() => {
                setLoading(false);
            });
    }, [getProgress, progressVersion]);

    useEffect(() => { load(); }, [load]);

    const skillData = (progress?.radarData?.points ?? []).map((p) => ({
        subject: p.tag,
        A: p.acceptanceRate ?? 0,
        fullMark: 100,
    }));


    const masteryData = [
        {
            label: "Easy",
            color: "#10b981",
            current: progress?.difficultyMastery?.easySolved ?? 0,
            total: progress?.difficultyMastery?.totalEasy ?? 0,
        },
        {
            label: "Medium",
            color: "#f59e0b",
            current: progress?.difficultyMastery?.mediumSolved ?? 0,
            total: progress?.difficultyMastery?.totalMedium ?? 0,
        },
        {
            label: "Hard",
            color: "#ef4444",
            current: progress?.difficultyMastery?.hardSolved ?? 0,
            total: progress?.difficultyMastery?.totalHard ?? 0,
        },
    ];


    const heatmapDots = useMemo(() => {
        const entries = progress?.heatmap ?? [];
        const countByDate = new Map();
        for (const e of entries) {
            if (!e?.date) continue;
            countByDate.set(e.date, e.count ?? 0);
        }

        // Render exactly last 365 days (GitHub-style window).
        // Use UTC to match backend DATE(submitted_at) -> YYYY-MM-DD reliably.
        const now = new Date();
        const pad2 = (n) => String(n).padStart(2, "0");
        const formatUTCISO = (d) =>
            `${d.getUTCFullYear()}-${pad2(d.getUTCMonth() + 1)}-${pad2(d.getUTCDate())}`;

        const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
        start.setUTCDate(start.getUTCDate() - 364); // inclusive: today + previous 364 days

        const counts = [];
        for (let i = 0; i < 365; i++) {
            const d = new Date(start);
            d.setUTCDate(start.getUTCDate() + i);
            const iso = formatUTCISO(d);
            counts.push(countByDate.get(iso) ?? 0);
        }

        const max = counts.length ? Math.max(...counts) : 0;
        return counts.map((count) => {
            if (!max || count <= 0) return "";
            // Map ratio to levels 0..2 (CSS defines active-0/1/2)
            const ratio = count / max;
            const level = Math.min(2, Math.floor(ratio * 3));
            return `active-${level}`;
        });
    }, [progress]);

    if (loading && !progress) {
        return (
            <div className="loader-container">
                <div className="modern-spinner"></div>
                <p>LOADING_PROGRESS...</p>
            </div>
        );
    }

    if (error && !progress) {
        return (
            <div className="loader-container">
                <p style={{ color: "#dc2626" }}>{error}</p>
            </div>
        );
    }

    return (
        <div className="progress-root">
            <div className="progress-content">
                <header className="progress-header">
                    <h1 className="welcome-msg">Your Learning Journey</h1>
                </header>

                {/* Heatmap */}
                <section className="glass-card heatmap-section">
                    <div className="card-header">
                        <div className="title-group">
                            <Activity size={18} color="#10b981" />
                            <h3>Submission Activity</h3>
                        </div>
                        <div className="heatmap-legend">
                            <span>Less</span>
                            <div className="legend-dots">
                                <span className="dot d1"></span>
                                <span className="dot d2"></span>
                                <span className="dot d3"></span>
                                <span className="dot d4"></span>
                            </div>
                            <span>More</span>
                        </div>
                    </div>

                    <div className="heatmap-placeholder">
                        <div className="mock-heatmap-grid">
                            {heatmapDots.map((status, i) => (
                                <div key={i} className={`h-dot ${status}`}></div>
                            ))}
                        </div>
                    </div>
                </section>

                <div className="grid-layout-bottom">
                    {/* Skill Radar */}
                    <div className="glass-card radar-section">
                        <div className="title-group">
                            <Flame size={18} color="#f59e0b" />
                            <h3>Skill Radar</h3>
                        </div>
                        <div className="chart-wrapper">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={skillData}>
                                    <PolarGrid stroke="#e2e8f0" />
                                    <PolarAngleAxis
                                        dataKey="subject"
                                        tick={{ fill: "#64748b", fontSize: 12 }}
                                    />
                                    <Radar
                                        name="Skills"
                                        dataKey="A"
                                        stroke="#6366f1"
                                        fill="#6366f1"
                                        fillOpacity={0.4}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Difficulty Mastery */}
                    <div className="glass-card mastery-section">
                        <div className="title-group">
                            <Target size={18} color="#a855f7" />
                            <h3>Difficulty Mastery</h3>
                        </div>
                        <div className="mastery-stack">
                            {masteryData.map((row, i) => (
                                <MasteryRow key={i} {...row} />
                            ))}
                        </div>
                        <div className="ai-insights">
                            <span className="ai-tag">AI INSIGHTS</span>
                            <p>
                                {progress?.aiInsight || "Keep solving to unlock personalized insights."}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Reusable MasteryRow component
const MasteryRow = ({ label, color, current, total }) => (
    <div className="mastery-row">
        <div className="m-labels">
            <span style={{ color }}>{label}</span>
            <span className="m-count">
                {current} / {total}
            </span>
        </div>
        <div className="m-bar-bg">
            <div
                className="m-bar-fill"
                style={{
                    width: `${total > 0 ? (current / total) * 100 : 0}%`,
                    backgroundColor: color
                }}
            ></div>
        </div>
    </div>
);

export default ProgressPage;