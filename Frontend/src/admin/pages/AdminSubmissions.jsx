import React, { useEffect, useState, useCallback } from "react";
import { X, Code2, Clock, MemoryStick, ListChecks, Sparkles } from "lucide-react";
import { fetchAdminSubmissionDetail } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext";
import VerdictBadge from "../components/VerdictBadge";
import PaginationBar from "../components/PaginationBar";
import "../../styles/admin.css";

const VERDICT_OPTIONS = [
  "", "ACCEPTED", "WRONG_ANSWER", "COMPILATION_ERROR",
  "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED"
];
const FILTER_DEBOUNCE_MS = 600;

export default function AdminSubmissions() {
  const { getSubmissions, submissionsVersion } = useAdminData();

  const [submissions, setSubmissions] = useState([]);
  const [verdict, setVerdict] = useState("");

  // Raw input values — update instantly as user types
  const [language, setLanguage] = useState("");
  const [userId, setUserId] = useState("");
  const [problemId, setProblemId] = useState("");

  // Debounced values — these actually trigger the fetch
  const [debouncedLanguage, setDebouncedLanguage] = useState("");
  const [debouncedUserId, setDebouncedUserId] = useState("");
  const [debouncedProblemId, setDebouncedProblemId] = useState("");

  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [totalElements, setTotalElements] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [detailTarget, setDetailTarget] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  // Debounce all three text filters
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedLanguage(language.trim()), FILTER_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [language]);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedUserId(userId.trim()), FILTER_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [userId]);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedProblemId(problemId.trim()), FILTER_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [problemId]);

  useEffect(() => { setPage(0); }, [verdict, debouncedLanguage, debouncedUserId, debouncedProblemId]);

  const loadSubmissions = useCallback(() => {
    setLoading(true);
    getSubmissions(page, 20, {
      verdict,
      language: debouncedLanguage,
      userId: debouncedUserId,
      problemId: debouncedProblemId,
    })
      .then(data => {
        setSubmissions(data.content);
        setTotalPages(data.totalPages);
        setTotalElements(data.totalElements);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [page, verdict, debouncedLanguage, debouncedUserId, debouncedProblemId, getSubmissions, submissionsVersion]);

  useEffect(() => { loadSubmissions(); }, [loadSubmissions]);

  const openDetail = (submission) => {
    setDetailTarget(submission);
    setDetail(null);
    setDetailError("");
    setDetailLoading(true);
    fetchAdminSubmissionDetail(submission.id)
      .then(setDetail)
      .catch(err => setDetailError(err.message))
      .finally(() => setDetailLoading(false));
  };

  return (
    <div className="admin-submissions-page">
      <h1 className="admin-page-title">Submission Management</h1>

      <div className="admin-filters-row">
        <select className="admin-select" value={verdict} onChange={e => setVerdict(e.target.value)}>
          <option value="">All Verdicts</option>
          {VERDICT_OPTIONS.filter(Boolean).map(v => (
            <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
          ))}
        </select>

        {/* ← bigger now */}
        <input
          className="admin-text-filter admin-text-filter-lg"
          placeholder="Language (partial match, e.g. python)"
          value={language}
          onChange={e => setLanguage(e.target.value)}
          style={{ cursor: "text" }}
        />

        <input
          className="admin-text-filter"
          placeholder="User ID"
          value={userId}
          onChange={e => setUserId(e.target.value)}
          style={{ cursor: "text" }}
        />

        <input
          className="admin-text-filter"
          placeholder="Problem ID"
          value={problemId}
          onChange={e => setProblemId(e.target.value)}
          style={{ cursor: "text" }}
        />
      </div>

      {error && <div className="admin-error-state">Failed to load submissions: {error}</div>}

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Problem</th>
              <th>Language</th>
              <th>Verdict</th>
              <th>Tests</th>
              <th>Time</th>
              <th>Memory</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map(s => (
              <tr
                key={s.id}
                className="admin-clickable-row"
                onClick={() => openDetail(s)}
              >
                <td className="admin-cell-strong">{s.username}</td>
                <td>{s.problemTitle}</td>
                <td>{s.languageName}</td>
                <td><VerdictBadge verdict={s.verdict} /></td>
                <td>{s.passedTests}/{s.totalTests}</td>
                <td>{s.executionTimeMs != null ? `${s.executionTimeMs}ms` : "—"}</td>
                <td>{s.memoryUsedKb != null ? `${s.memoryUsedKb}KB` : "—"}</td>
                <td>{s.submittedAt ? new Date(s.submittedAt).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && submissions.length === 0 && (
          <div className="admin-empty-state">No submissions found.</div>
        )}

        <PaginationBar
          page={page}
          totalPages={totalPages}
          totalElements={totalElements}
          onPageChange={setPage}
          loading={loading}
        />
      </div>

      {detailTarget && (
        <div className="admin-modal-backdrop" onClick={() => setDetailTarget(null)}>
          <div className="admin-submission-detail-modal" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <div>
                <h3>{detailTarget.problemTitle}</h3>
                <p className="admin-detail-subtitle">
                  by {detailTarget.username} · {detailTarget.languageName}
                </p>
              </div>
              <button className="admin-modal-close" onClick={() => setDetailTarget(null)}><X size={18} /></button>
            </div>

            {detailLoading && <p className="admin-page-placeholder">Loading submission...</p>}
            {detailError && <p className="admin-inline-error">{detailError}</p>}

            {detail && (
              <div className="admin-submission-detail-body">
                <div className="admin-detail-stats-row">
                  <div className="admin-detail-stat">
                    <VerdictBadge verdict={detail.verdict} />
                  </div>
                  <div className="admin-detail-stat">
                    <ListChecks size={14} /> {detail.passedTests}/{detail.totalTests} tests
                  </div>
                  <div className="admin-detail-stat">
                    <Clock size={14} /> {detail.executionTimeMs ?? "—"}ms
                  </div>
                  <div className="admin-detail-stat">
                    <MemoryStick size={14} /> {detail.memoryUsedKb ?? "—"}KB
                  </div>
                </div>

                <div className="admin-detail-section">
                  <h4><Code2 size={14} /> Source Code</h4>
                  <pre className="admin-code-block"><code>{detail.sourceCode}</code></pre>
                </div>

                {detail.aiErrorType && (
                  <div className="admin-detail-section">
                    <h4><Sparkles size={14} /> AI Feedback</h4>
                    <p className="admin-ai-error-type">{detail.aiErrorType}</p>
                    <p className="admin-ai-explanation">{detail.aiExplanation}</p>
                  </div>
                )}

                {detail.testResults?.length > 0 && (
                  <div className="admin-detail-section">
                    <h4><ListChecks size={14} /> Test Results</h4>
                    <div className="admin-test-results-list">
                      {detail.testResults.map((t, idx) => (
                        <div key={idx} className={`admin-test-result-row ${t.passed ? "passed" : "failed"}`}>
                          <span>Test {idx + 1}</span>
                          <span>{t.passed ? "✓ Passed" : "✗ Failed"}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}