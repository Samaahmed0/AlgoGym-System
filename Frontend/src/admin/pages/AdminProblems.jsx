import React, { useEffect, useState, useCallback, useRef } from "react";
import { Search, Eye, EyeOff, Trash2, Upload, X, CheckCircle2, AlertCircle } from "lucide-react";
import { toggleProblemVisibility, deleteAdminProblem, bulkImportProblems } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext"; // ← add
import ConfirmModal from "../components/ConfirmModal";
import PaginationBar from "../components/PaginationBar";
import "../../styles/admin.css";

const SEARCH_DEBOUNCE_MS = 600;
const DIFFICULTIES = ["", "Easy", "Medium", "Hard", "Expert"];
const VISIBLE_OPTIONS = [
  { value: "all", label: "All" },
  { value: "visible", label: "Visible" },
  { value: "hidden", label: "Hidden" },
];

export default function AdminProblems() {
  const { getProblems, invalidateProblems, problemsVersion } = useAdminData(); // ← add

  const [problems, setProblems] = useState([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [visible, setVisible] = useState("all");
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [totalElements, setTotalElements] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [importOpen, setImportOpen] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [search]);

  useEffect(() => { setPage(0); }, [debouncedSearch, difficulty, visible]);

  const loadProblems = useCallback(() => {
    setLoading(true);
    getProblems(page, 20, debouncedSearch, difficulty, visible)
      .then(data => {
        setProblems(data.content);
        setTotalPages(data.totalPages);
        setTotalElements(data.totalElements);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [page, debouncedSearch, difficulty, visible, getProblems, problemsVersion]);

  useEffect(() => { loadProblems(); }, [loadProblems]);

  const handleToggleVisibility = async (problem) => {
    try {
      await toggleProblemVisibility(problem.id, !problem.isVisible);
      invalidateProblems(); // ← refresh after mutation
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteAdminProblem(deleteTarget.id);
      setDeleteTarget(null);
      invalidateProblems(); // ← refresh after mutation
    } catch (err) {
      setActionError(err.message);
      setDeleteTarget(null);
    }
  };

  // ... rest of JSX unchanged, except BulkImportModal's onImported:
  // onImported={() => { setImportOpen(false); invalidateProblems(); }}

  return (
    <div className="admin-problems-page">
      <div className="admin-page-header-row">
        <h1 className="admin-page-title">Problem Management</h1>
        <button className="admin-btn-primary" onClick={() => setImportOpen(true)}>
          <Upload size={16} /> Bulk Import
        </button>
      </div>

      {actionError && (
        <div className="admin-inline-error">
          {actionError}
          <button onClick={() => setActionError("")}><X size={14} /></button>
        </div>
      )}

      <div className="admin-filters-row">
        <div className="admin-search-bar">
          <Search size={16} className="admin-search-icon" />
          <input
            type="search"
            placeholder="Search by title..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ cursor: "text" }}
          />
        </div>

        <select className="admin-select" value={difficulty} onChange={e => setDifficulty(e.target.value)}>
          <option value="">All Difficulties</option>
          {DIFFICULTIES.filter(Boolean).map(d => <option key={d} value={d}>{d}</option>)}
        </select>

        <div className="admin-segmented">
          {VISIBLE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              className={`admin-segmented-btn ${visible === opt.value ? "active" : ""}`}
              onClick={() => setVisible(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="admin-error-state">Failed to load problems: {error}</div>}

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Rating</th>
              <th>Tags</th>
              <th>Submissions</th>
              <th>Acceptance</th>
              <th>Visibility</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {problems.map(p => (
              <tr key={p.id}>
                <td className="admin-cell-strong">{p.title}</td>
                <td>{p.rating ?? "—"}</td>
                <td>
                  <div className="admin-tag-row">
                    {(p.tags || []).slice(0, 2).map((t, idx) => (
                      <span key={idx} className="admin-tag-chip">{t}</span>
                    ))}
                    {p.tags && p.tags.length > 2 && (
                      <span className="admin-tag-chip muted">+{p.tags.length - 2}</span>
                    )}
                  </div>
                </td>
                <td>{p.totalSubmissions ?? 0}</td>
                <td>{p.acceptanceRate != null ? `${p.acceptanceRate}%` : "—"}</td>
                <td>
                  <span className={`admin-visibility-badge ${p.isVisible ? "visible" : "hidden"}`}>
                    {p.isVisible ? "Visible" : "Hidden"}
                  </span>
                </td>
                <td>
                  <div className="admin-row-actions">
                    <button
                      className="admin-icon-btn"
                      title={p.isVisible ? "Hide problem" : "Show problem"}
                      onClick={() => handleToggleVisibility(p)}
                    >
                      {p.isVisible ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                    <button
                      className="admin-icon-btn danger"
                      title="Delete problem"
                      onClick={() => setDeleteTarget(p)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && problems.length === 0 && (
          <div className="admin-empty-state">No problems found.</div>
        )}

        <PaginationBar
          page={page}
          totalPages={totalPages}
          totalElements={totalElements}
          onPageChange={setPage}
          loading={loading}
        />
      </div>

      {deleteTarget && (
        <ConfirmModal
          title="Delete problem?"
          message={`This will permanently delete "${deleteTarget.title}". This cannot be undone.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {importOpen && (
        <BulkImportModal
           onClose={() => setImportOpen(false)}
              onImported={() => { setImportOpen(false); invalidateProblems(); }}
        />
      )}
    </div>
  );
}

function BulkImportModal({ onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [format, setFormat] = useState("json");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleSubmit = async () => {
    if (!file) {
      setError("Please choose a file first");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const res = await bulkImportProblems(file, format);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-import-modal" onClick={e => e.stopPropagation()}>
        <div className="admin-modal-header">
          <h3>Bulk Import Problems</h3>
          <button className="admin-modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        {!result ? (
          <>
            <div className="admin-segmented" style={{ marginBottom: 16 }}>
              <button className={`admin-segmented-btn ${format === "json" ? "active" : ""}`} onClick={() => setFormat("json")}>JSON</button>
              <button className={`admin-segmented-btn ${format === "csv" ? "active" : ""}`} onClick={() => setFormat("csv")}>CSV</button>
            </div>

            <div className="admin-file-drop" onClick={() => fileInputRef.current?.click()}>
              <Upload size={24} />
              <p>{file ? file.name : `Click to choose a .${format} file`}</p>
              <input
                ref={fileInputRef}
                type="file"
                accept={format === "json" ? ".json" : ".csv"}
                style={{ display: "none" }}
                onChange={e => setFile(e.target.files[0])}
              />
            </div>

            {error && <p className="admin-inline-error" style={{ marginTop: 12 }}>{error}</p>}

            <div className="admin-confirm-actions" style={{ marginTop: 20 }}>
              <button className="admin-btn-secondary" onClick={onClose}>Cancel</button>
              <button className="admin-btn-primary" onClick={handleSubmit} disabled={uploading}>
                {uploading ? "Importing..." : "Import"}
              </button>
            </div>
          </>
        ) : (
          <div className="admin-import-result">
            <CheckCircle2 size={32} color="#10b981" />
            <p><strong>{result.imported}</strong> imported, <strong>{result.skipped}</strong> skipped, <strong>{result.failed}</strong> failed</p>

            {result.errors?.length > 0 && (
              <div className="admin-import-errors">
                {result.errors.map((e, idx) => (
                  <div key={idx} className="admin-import-error-row">
                    <AlertCircle size={13} /> {e}
                  </div>
                ))}
              </div>
            )}

            <button className="admin-btn-primary" onClick={onImported} style={{ marginTop: 16 }}>
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}