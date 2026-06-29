import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, CheckCircle2, Filter, ChevronLeft, ChevronRight, Search, HelpCircle } from "lucide-react";
import { useUserData } from "../UserDataContext";
import "../styles/problems.css";

const SEARCH_DEBOUNCE_MS = 1000;

// Sliding window pagination — shows 5 pages at a time around current page
function getPaginationWindow(current, total) {
  const window = 5;
  let start = Math.max(1, current - Math.floor(window / 2));
  let end = start + window - 1;
  if (end > total) {
    end = total;
    start = Math.max(1, end - window + 1);
  }
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}

export default function ProblemsPage() {
  const { getProblems, getProblemTags, problemsVersion } = useUserData();
  const [problems, setProblems] = useState([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [difficulty, setDifficulty] = useState([]);
  const [topic, setTopic] = useState([]);
  const [statusFilter, setStatusFilter] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [availableTopics, setAvailableTopics] = useState([]);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [tagsError, setTagsError] = useState(null);
  const pageSize = 10;
  const scrollRef = useRef(null);
  const navigate = useNavigate();

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [search]);

  // Fetch problems
  const loadProblems = useCallback(() => {
    setLoading(true);
    setError(null);
    getProblems(page - 1, pageSize, {
      title: debouncedSearch,
      difficulty,
      topic,
      status: statusFilter,
    })
      .then(data => {
        setProblems(data.content);
        setTotalPages(data.totalPages);
      })
      .catch(err => {
        console.error("Error loading problems:", err);
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
        setInitialLoad(false);
      });
  }, [page, debouncedSearch, difficulty, topic, statusFilter, getProblems, problemsVersion]);

  useEffect(() => { loadProblems(); }, [loadProblems]);

  const loadTags = useCallback(() => {
    setTagsLoading(true);
    setTagsError(null);
    getProblemTags()
      .then(setAvailableTopics)
      .catch(err => {
        console.error("Error loading topics:", err);
        setTagsError(err.message || "Failed to load topics");
      })
      .finally(() => setTagsLoading(false));
  }, [getProblemTags, problemsVersion]);

  useEffect(() => { loadTags(); }, [loadTags]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, difficulty, topic, statusFilter]);

  const availableDifficulties = ["Easy", "Medium", "Hard"];
  const availableStatuses = ["solved", "attempted", "unsolved"];

  const toggleFilter = (value, setter, state) => {
    setter(state.includes(value) ? state.filter(v => v !== value) : [...state, value]);
  };

  // Difficulty is intended as a single-choice filter (prevents "Hard" accidentally also including "Medium").
  const toggleDifficulty = (value) => {
    setDifficulty((prev) => (prev.length === 1 && prev[0] === value ? [] : [value]));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "solved":    return <CheckCircle2 className="status-clock solved" size={22} />;
      case "attempted": return <Clock className="status-clock midway" size={22} />;
      default:          return <Clock className="status-clock grey" size={22} />;
    }
  };

  const pageWindow = getPaginationWindow(page, totalPages);

  if (initialLoad) return (
    <div className="loader-container">
      <div className="modern-spinner"></div>
      <p>SYNCHRONIZING_DATABASE...</p>
    </div>
  );

  if (error) return (
    <div className="loader-container">
      <div className="error-message">
        <p>Error: {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    </div>
  );

  return (
    <main className="problems-view">
      <div className="background-mesh"></div>

      <div className="view-content">
        <header className="view-header">
          <div className="header-text">
            <h1 className="main-title-gradient">Problemset</h1>
            <p className="subtitle-text">Explore problems by difficulty and topic to strengthen your algorithms.</p>
          </div>
        </header>

        <div className="bubble-navigation">
          <div className="bubble-scroll-wrapper" ref={scrollRef}>
            <button
              className={`filter-bubble-item ${topic.length === 0 ? "active" : ""}`}
              onClick={() => setTopic([])}
            >
              All Topics
            </button>
            {tagsLoading && (
              <span className="tags-status-msg">
                <span className="inline-spinner tags-inline-spinner" />
                Loading topics…
              </span>
            )}
            {tagsError && !tagsLoading && (
              <span className="tags-status-msg tags-status-error">
                {tagsError}
                <button type="button" className="tags-retry-btn" onClick={loadTags}>
                  Retry
                </button>
              </span>
            )}
            {!tagsLoading && !tagsError && availableTopics.map(t => (
              <button
                key={t}
                className={`filter-bubble-item ${topic.includes(t) ? "active" : ""}`}
                onClick={() => toggleFilter(t, setTopic, topic)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Search + Filter button on same row */}
        <section className="interaction-layer">
          <div className="search-bar-modern">
            <Search size={18} className="search-icon-dim" />
            <input
              type="search"
              enterKeyHint="search"
              autoComplete="off"
              spellCheck="false"
              placeholder="Search problems by title..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Subtle inline indicator */}
          <div className="loading-indicator-container">
            {loading && !initialLoad && !search && (
              <div className="inline-spinner" />
            )}
          </div>

          {/* Filter button */}
          <button
            className={`filter-toggle-btn ${showFilters ? 'is-active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter size={16} />
            <span>Advanced Filters</span>
          </button>
        </section>

        {showFilters && (
          <div className="advanced-filter-panel">
            <div className="filter-inner-grid">
              <div className="filter-section">
                <span className="section-label">DIFFICULTY</span>
                <div className="pill-selection-row">
                  {availableDifficulties.map(d => (
                    <span
                      key={d}
                      className={`selection-pill ${difficulty.includes(d) ? "active" : ""}`}
                      onClick={() => toggleDifficulty(d)}
                    >
                      {d}
                    </span>
                  ))}
                </div>
              </div>
              <div className="filter-section">
                <span className="section-label">COMPLETION STATUS</span>
                <div className="pill-selection-row">
                  {availableStatuses.map(s => (
                    <span
                      key={s}
                      className={`selection-pill ${statusFilter.includes(s) ? "active" : ""}`}
                      onClick={() => toggleFilter(s, setStatusFilter, statusFilter)}
                    >
                      {s.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className={`table-container-glass ${loading ? "table-updating" : ""}`}>
          <table className="problems-data-table">
            <thead>
              <tr>
                <th className="th-status">Status</th>
                <th className="th-title">Title</th>
                <th className="th-tags">Taxonomy</th>
                <th className="th-diff">Difficulty</th>
                <th className="th-acc">Acceptance</th>
              </tr>
            </thead>
            <tbody>
              {problems.map(p => (
                <tr
                  key={p.id}
                  className="problem-table-row"
                  onClick={() => navigate(`/problems/${p.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="td-status-icon">{getStatusIcon(p.status)}</td>
                  <td className="td-title-text">
                    <span className="problem-name">{p.title}</span>
                  </td>
                  <td className="td-tags-cluster">
                    <div className="tag-flex-row">
                      {(p.tags || []).slice(0, 3).map((t, idx) => (
                        <span key={idx} className="neon-problem-tag">{t}</span>
                      ))}
                      {p.tags && p.tags.length > 3 && (
                        <div className="overflow-tag-wrapper">
                          <span className="overflow-indicator">+{p.tags.length - 3}</span>
                          <div className="tag-hover-tooltip">
                            {p.tags.slice(3).join(" • ")}
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="td-difficulty-badge">
                    <span className={`diff-pill ${p.difficulty?.toLowerCase() || 'easy'}`}>
                      {p.difficulty || 'Easy'}
                    </span>
                  </td>
                  <td className="td-acceptance-rate">
                    <span className="acceptance-value">{p.acceptance || 0}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {problems.length === 0 && !loading && (
            <div className="no-results-state">
              <HelpCircle size={40} color="var(--text-muted)" />
              <p>No problems found matching these criteria.</p>
            </div>
          )}

          {/* Sliding window pagination */}
          <div className="pagination-footer">
            <div className="pagination-controls">

            {/* Prev arrow */}
             <button
                className="pag-nav-arrow"
                disabled={page === 1 || loading}
                onClick={() => setPage(p => p - 1)}
             >
             <ChevronLeft size={20} />
             </button>

              {/* First page jump */}
              {pageWindow[0] > 1 && (
                <>
                  <button className="pag-num-btn" onClick={() => setPage(1)} disabled={loading}>1</button>
                  {pageWindow[0] > 2 && <span className="pag-ellipsis">...</span>}
                </>
              )}

              {/* Page window */}
              {pageWindow.map(p => (
                <button
                  key={p}
                  className={`pag-num-btn ${page === p ? "is-active" : ""}`}
                  onClick={() => setPage(p)}
                  disabled={loading}
                >
                  {p}
                </button>
              ))}

              {/* Last page jump */}
              {pageWindow[pageWindow.length - 1] < totalPages && (
                <>
                  {pageWindow[pageWindow.length - 1] < totalPages - 1 && (
                    <span className="pag-ellipsis">...</span>
                  )}
                  <button className="pag-num-btn" onClick={() => setPage(totalPages)} disabled={loading}>
                    {totalPages}
                  </button>
                </>
              )}

              {/* Next arrow */}
              <button
                className="pag-nav-arrow"
                disabled={page === totalPages || loading}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight size={20} />
              </button>

            </div>
          </div>
        </div>
      </div>
    </main>
  );
}