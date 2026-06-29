import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BarChart3,
  Lightbulb,
  TrendingDown,
  X,
  ListOrdered,
} from "lucide-react";
import { useUserData } from "../UserDataContext";
import { difficultyClass, flattenRecommendations } from "../utils/recommended.utils";
import "../styles/recommended.css";
import "../styles/recommended-explore.css";

const HOW_IT_WORKS = [
  {
    step: "01",
    icon: BarChart3,
    title: "We analyze your submissions",
    desc: "AlgoGym tracks which topics you solve correctly and where you struggle.",
  },
  {
    step: "02",
    icon: TrendingDown,
    title: "We detect weak areas",
    desc: "GPPKT estimates mastery per topic — your weakest five are surfaced first.",
  },
  {
    step: "03",
    icon: Lightbulb,
    title: "You get matched problems",
    desc: "Each suggestion targets a specific weakness so your practice time is focused.",
  },
];

function formatLastUpdated(iso) {
  if (!iso) return "Recently";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "Recently";
  }
}

/** Preview card accents — match design mock (DP / Graph / Bit) */
const PREVIEW_WEAK_ACCENTS = ["#a855f7", "#6366f1", "#d946ef"];

function weakAreaStatus(pct) {
  if (pct == null) return "Recommended practice";
  if (pct < 40) return "Needs focus";
  if (pct < 55) return "Room to grow";
  return "Building strength";
}

function WeakAreaChip({ area }) {
  const pct = area.accuracy ?? 0;
  const hasPct = area.accuracy != null;

  return (
    <div className="rec-overview-chip" style={{ "--chip-accent": area.accent }}>
      <span className="rec-overview-name">{area.name}</span>
      {hasPct && <span className="rec-overview-pct">{pct}%</span>}
      <div className="rec-overview-bar" aria-hidden={!hasPct}>
        <div
          className="rec-overview-fill"
          style={{ width: hasPct ? `${Math.min(100, Math.max(0, pct))}%` : "0%" }}
        />
      </div>
      <span className="rec-overview-hint">{weakAreaStatus(area.accuracy)}</span>
    </div>
  );
}

function mapApiToAreas(apiData) {
  return (apiData?.weakAreas ?? []).map((area) => ({
    ...area,
    accuracy: area.accuracy ?? null,
    recommendations: (area.recommendations ?? []).map((rec) => ({
      title: rec.title,
      difficulty: rec.difficulty,
      topic: rec.topic,
      reason: rec.reason,
      resolvedId: rec.problemId,
    })),
  }));
}

export default function RecommendedPage() {
  const navigate = useNavigate();
  const { getRecommendations, recommendationsVersion } = useUserData();
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weakAreasModalOpen, setWeakAreasModalOpen] = useState(false);

  const loadRecommendations = useCallback(() => {
    setLoading(true);
    getRecommendations()
      .then((data) => {
        setApiData(data);
        setError(null);
      })
      .catch((err) => {
        console.error("Failed to load recommendations:", err);
        setError(err.message || "Failed to load recommendations");
        setApiData(null);
      })
      .finally(() => setLoading(false));
  }, [getRecommendations, recommendationsVersion]);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const resolvedAreas = useMemo(() => mapApiToAreas(apiData), [apiData]);

  const flatProblems = useMemo(
    () => flattenRecommendations(resolvedAreas),
    [resolvedAreas]
  );

  const allWeakAreas = useMemo(
    () =>
      [...resolvedAreas].sort((a, b) => (a.accuracy ?? 100) - (b.accuracy ?? 100)),
    [resolvedAreas]
  );

  const previewWeakAreas = useMemo(
    () =>
      allWeakAreas.slice(0, 3).map((area, index) => ({
        ...area,
        accent: PREVIEW_WEAK_ACCENTS[index] ?? area.accent,
      })),
    [allWeakAreas]
  );

  const summary = useMemo(
    () => ({
      totalPicks: apiData?.totalPicks ?? 0,
      weakAreas: apiData?.weakAreasCount ?? resolvedAreas.length,
      lastUpdated: formatLastUpdated(apiData?.lastUpdated),
    }),
    [apiData, resolvedAreas.length]
  );

  useEffect(() => {
    if (!weakAreasModalOpen) return undefined;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e) => {
      if (e.key === "Escape") setWeakAreasModalOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [weakAreasModalOpen]);

  const goToProblem = (id) => {
    if (id) navigate(`/problems/${encodeURIComponent(id)}`);
  };

  if (loading && !apiData) {
    return (
      <main className="recommended-view">
        <div className="rec-view-content">
          <p className="subtitle-text">Loading recommendations…</p>
        </div>
      </main>
    );
  }

  if (error && !apiData) {
    return (
      <main className="recommended-view">
        <div className="rec-view-content">
          <p className="subtitle-text" style={{ color: "#dc2626" }}>{error}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="recommended-view">
      <div className="rec-background-mesh" />

      <div className="rec-view-content">
        <header className="view-header">
          <div className="header-text">
            <span className="rec-page-label">Personalized practice</span>
            <h1 className="main-title-gradient">Recommended for You</h1>
            <p className="subtitle-text">
              This page shows <strong>coding problems chosen for your weak topics</strong>.
            </p>
          </div>
        </header>

        <section className="rec-how-section" aria-labelledby="how-it-works-title">
          <h2 id="how-it-works-title" className="rec-section-heading">
            How recommendations work
          </h2>
          <div className="rec-how-grid">
            {HOW_IT_WORKS.map(({ step, icon: Icon, title, desc }) => (
              <div key={step} className="rec-how-card">
                <span className="rec-how-step">{step}</span>
                <div className="rec-how-icon">
                  <Icon size={20} />
                </div>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {resolvedAreas.length === 0 ? (
          <section className="rec-overview-section">
            <p className="rec-section-sub">
              No recommendations yet. Keep solving problems — personalized suggestions will
              appear here after the next AI refresh.
            </p>
          </section>
        ) : (
          <>
            <section className="rec-overview-section" aria-labelledby="weak-areas-title">
              <div className="rec-overview-head">
                <h2 id="weak-areas-title" className="rec-section-heading">
                  Your weak areas right now
                </h2>
                {allWeakAreas.length > 3 && (
                  <button
                    type="button"
                    className="rec-see-more-btn"
                    onClick={() => setWeakAreasModalOpen(true)}
                  >
                    See more
                    <ArrowRight size={14} />
                  </button>
                )}
              </div>

              <div className="rec-overview-grid">
                {previewWeakAreas.map((area) => (
                  <WeakAreaChip key={area.id} area={area} />
                ))}
              </div>
            </section>

            <section className="rec-flat-section" aria-labelledby="flat-list-title">
              <div className="rec-flat-head">
                <div>
                  <h2 id="flat-list-title" className="rec-section-heading">
                    <ListOrdered size={22} className="rec-flat-icon" />
                    All recommended problems
                  </h2>
                  <p className="rec-section-sub rec-flat-sub">
                    Up to {summary.totalPicks} active problems — solved correctly are
                    replaced automatically · Updated {summary.lastUpdated}
                  </p>
                </div>
              </div>

              <div className="rec-flat-panel">
                {flatProblems.map((problem, i) => {
                  const clickable = Boolean(problem.resolvedId);
                  const isFirst = i === 0;

                  return (
                    <article
                      key={`${problem.weakAreaId}-${problem.resolvedId ?? problem.title}-${i}`}
                      className={`rec-flat-row ${isFirst ? "is-next-up" : ""} ${clickable ? "" : "is-disabled"}`}
                      style={{ "--section-accent": problem.weakAreaAccent }}
                      onClick={() => clickable && goToProblem(problem.resolvedId)}
                      role={clickable ? "button" : undefined}
                      tabIndex={clickable ? 0 : undefined}
                      onKeyDown={(e) => {
                        if (!clickable) return;
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          goToProblem(problem.resolvedId);
                        }
                      }}
                    >
                      <div className="rec-flat-index-col">
                        <span className="rec-flat-index">{problem.listIndex}</span>
                        {i < flatProblems.length - 1 && (
                          <span className="rec-flat-connector" />
                        )}
                      </div>

                      <div className="rec-flat-body">
                        <div className="rec-flat-top">
                          <h3 className="rec-flat-title">{problem.title}</h3>
                          <span
                            className={`rec-difficulty-pill ${difficultyClass(problem.difficulty)}`}
                          >
                            {problem.difficulty}
                          </span>
                        </div>

                        <div className="rec-flat-meta">
                          <span
                            className="rec-flat-weak-tag"
                            style={{
                              color: problem.weakAreaAccent,
                              borderColor: `${problem.weakAreaAccent}33`,
                              background: `${problem.weakAreaAccent}12`,
                            }}
                          >
                            {problem.weakAreaName}
                          </span>
                          <span className="rec-flat-topic">{problem.topic}</span>
                        </div>

                        <p className="rec-flat-reason">{problem.reason}</p>
                      </div>

                      <button
                        type="button"
                        className="rec-open-btn rec-flat-open"
                        disabled={!clickable}
                        onClick={(e) => {
                          e.stopPropagation();
                          goToProblem(problem.resolvedId);
                        }}
                      >
                        {isFirst ? "Start here" : "Open"}
                        <ArrowRight size={15} />
                      </button>
                    </article>
                  );
                })}
              </div>
            </section>
          </>
        )}
      </div>

      {weakAreasModalOpen && (
        <div
          className="rec-modal-backdrop"
          onClick={() => setWeakAreasModalOpen(false)}
          role="presentation"
        >
          <div
            className="rec-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="weak-areas-modal-title"
          >
            <div className="rec-modal-header">
              <div>
                <h2 id="weak-areas-modal-title" className="rec-modal-title">
                  All weak areas
                </h2>
                <p className="rec-modal-sub">
                  {allWeakAreas.length} topics ranked by mastery — lowest first
                </p>
              </div>
              <button
                type="button"
                className="rec-modal-close"
                onClick={() => setWeakAreasModalOpen(false)}
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            <div className="rec-modal-body">
              {allWeakAreas.map((area, index) => (
                <div key={area.id} className="rec-modal-row">
                  <span className="rec-modal-rank">{index + 1}</span>
                  <div className="rec-modal-row-main">
                    <div className="rec-modal-row-top">
                      <span className="rec-modal-row-name">{area.name}</span>
                      {area.accuracy != null && (
                        <span className="rec-modal-row-pct" style={{ color: area.accent }}>
                          {area.accuracy}% mastery
                        </span>
                      )}
                    </div>
                    {area.accuracy != null && (
                      <div className="rec-overview-bar">
                        <div
                          className="rec-overview-fill"
                          style={{ width: `${area.accuracy}%`, background: area.accent }}
                        />
                      </div>
                    )}
                    {area.insight && (
                      <p className="rec-modal-row-insight">{area.insight}</p>
                    )}
                  </div>
                  <span className="rec-modal-row-tag">{weakAreaStatus(area.accuracy)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
