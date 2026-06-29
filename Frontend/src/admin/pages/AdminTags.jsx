import React, { useEffect, useState, useCallback } from "react";
import { Search, Pencil, X, TrendingUp, Tags as TagsIcon } from "lucide-react";
import { renameTag } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext";
import "../../styles/admin.css";

export default function AdminTags() {
  const { getTags, invalidateTags, tagsVersion } = useAdminData();

  const [mode, setMode] = useState("all"); // "all" | "most-attempted"
  const [tags, setTags] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [renameTarget, setRenameTarget] = useState(null);
  const [newTagName, setNewTagName] = useState("");
  const [renaming, setRenaming] = useState(false);
  const [renameError, setRenameError] = useState("");
  const [renameSuccess, setRenameSuccess] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    getTags(mode)
      .then(data => {
        setTags(data);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [mode, getTags, tagsVersion]);

  useEffect(() => { load(); }, [load]);

  const filteredTags = tags.filter(t =>
    t.tag.toLowerCase().includes(search.toLowerCase())
  );

  const openRename = (tag) => {
    setRenameTarget(tag);
    setNewTagName(tag.tag);
    setRenameError("");
  };

  const handleRename = async () => {
    if (!renameTarget) return;
    const trimmed = newTagName.trim();
    if (!trimmed) {
      setRenameError("Tag name cannot be empty");
      return;
    }
    if (trimmed === renameTarget.tag) {
      setRenameTarget(null);
      return;
    }

    setRenaming(true);
    setRenameError("");
    try {
      const result = await renameTag(renameTarget.tag, trimmed);
      setRenameTarget(null);
      invalidateTags();
      setRenameSuccess(`Renamed "${renameTarget.tag}" → "${trimmed}" across ${result.problemsUpdated} problems.`);
      setTimeout(() => setRenameSuccess(""), 4000);
    } catch (err) {
      setRenameError(err.message || "Rename failed");
    } finally {
      setRenaming(false);
    }
  };

  return (
    <div className="admin-tags-page">
      <div className="admin-page-header-row">
        <h1 className="admin-page-title">Tag Management</h1>
        <div className="admin-segmented">
          <button
            className={`admin-segmented-btn ${mode === "all" ? "active" : ""}`}
            onClick={() => setMode("all")}
          >
            All Tags
          </button>
          <button
            className={`admin-segmented-btn ${mode === "most-attempted" ? "active" : ""}`}
            onClick={() => setMode("most-attempted")}
          >
            <TrendingUp size={13} style={{ marginRight: 4 }} /> Most Attempted
          </button>
        </div>
      </div>

      {renameSuccess && (
        <div className="admin-success-banner">{renameSuccess}</div>
      )}

      <div className="admin-search-bar">
        <Search size={16} className="admin-search-icon" />
        <input
          type="search"
          placeholder="Search tags..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ cursor: "text" }}
        />
      </div>

      {error && <div className="admin-error-state">Failed to load tags: {error}</div>}

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Problems</th>
              <th>User Submissions</th>
              <th>User Solved</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredTags.map((t, idx) => (
              <tr key={idx}>
                <td>
                  <span className="admin-tag-chip-lg">
                    <TagsIcon size={12} /> {t.tag}
                  </span>
                </td>
                <td>{t.problemCount}</td>
                <td>{t.totalUserSubmissions}</td>
                <td>{t.totalUserSolved}</td>
                <td>
                  <button className="admin-icon-btn" title="Rename tag" onClick={() => openRename(t)}>
                    <Pencil size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && filteredTags.length === 0 && (
          <div className="admin-empty-state">No tags found.</div>
        )}
      </div>

      {renameTarget && (
        <div className="admin-modal-backdrop" onClick={() => setRenameTarget(null)}>
          <div className="admin-rename-modal" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3>Rename Tag</h3>
              <button className="admin-modal-close" onClick={() => setRenameTarget(null)}><X size={18} /></button>
            </div>

            <p className="admin-rename-hint">
              This will rename <strong>"{renameTarget.tag}"</strong> across all{" "}
              <strong>{renameTarget.problemCount}</strong> problem(s) that use it.
            </p>

            <input
              className="admin-rename-input"
              value={newTagName}
              onChange={e => setNewTagName(e.target.value)}
              autoFocus
              style={{ cursor: "text" }}
            />

            {renameError && <p className="admin-inline-error" style={{ marginTop: 10 }}>{renameError}</p>}

            <div className="admin-confirm-actions" style={{ marginTop: 20 }}>
              <button className="admin-btn-secondary" onClick={() => setRenameTarget(null)}>Cancel</button>
              <button className="admin-btn-primary" onClick={handleRename} disabled={renaming}>
                {renaming ? "Renaming..." : "Rename"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}