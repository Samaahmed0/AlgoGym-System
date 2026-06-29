import React, { useEffect, useState, useCallback } from "react";
import { Search, Trash2, Shield, ShieldCheck, History, X } from "lucide-react";
import { updateUserRole, deleteAdminUser, fetchRoleChangeLog } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext"; // ← add
import { useAuth } from "../../Auth/auth.context";
import ConfirmModal from "../components/ConfirmModal";
import PaginationBar from "../components/PaginationBar";
import "../../styles/admin.css";

const SEARCH_DEBOUNCE_MS = 600;

export default function AdminUsers() {
  const { user: currentUser } = useAuth();
  const { getUsers, invalidateUsers, usersVersion } = useAdminData(); // ← add

  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [totalElements, setTotalElements] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [roleChangeTarget, setRoleChangeTarget] = useState(null);
  const [logOpen, setLogOpen] = useState(false);
  const [logEntries, setLogEntries] = useState([]);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [search]);

  useEffect(() => { setPage(0); }, [debouncedSearch]);

  const loadUsers = useCallback(() => {
    setLoading(true);
    getUsers(page, 10, debouncedSearch)
      .then(data => {
        setUsers(data.content);
        setTotalPages(data.totalPages);
        setTotalElements(data.totalElements);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
    // usersVersion in deps means: when invalidated, this re-runs even with same page/search
  }, [page, debouncedSearch, getUsers, usersVersion]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteAdminUser(deleteTarget.id);
      setDeleteTarget(null);
      invalidateUsers(); // ← clears cache + triggers refetch via usersVersion
    } catch (err) {
      setActionError(err.message);
      setDeleteTarget(null);
    }
  };

  const handleRoleChange = async (newRole) => {
    if (!roleChangeTarget) return;
    try {
      await updateUserRole(roleChangeTarget.id, newRole);
      setRoleChangeTarget(null);
      invalidateUsers(); // ← same here
    } catch (err) {
      setActionError(err.message);
      setRoleChangeTarget(null);
    }
  };

  const openLog = () => {
    fetchRoleChangeLog().then(setLogEntries).catch(err => setActionError(err.message));
    setLogOpen(true);
  };


  return (
    <div className="admin-users-page">
      <div className="admin-page-header-row">
        <h1 className="admin-page-title">User Management</h1>
        <button className="admin-btn-secondary" onClick={openLog}>
          <History size={16} /> Role Change Log
        </button>
      </div>

      {actionError && (
        <div className="admin-inline-error">
          {actionError}
          <button onClick={() => setActionError("")}><X size={14} /></button>
        </div>
      )}

      <div className="admin-search-bar">
        <Search size={16} className="admin-search-icon" />
        <input
          type="search"
          placeholder="Search by username or email..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ cursor: "text" }}
        />
      </div>

      {error && <div className="admin-error-state">Failed to load users: {error}</div>}

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Skill Level</th>
              <th>Solved</th>
              <th>Streak</th>
              <th>Acceptance</th>
              <th>Rating</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td className="admin-cell-strong">{u.username}</td>
                <td>{u.email}</td>
                <td>
                  <span className={`admin-role-badge ${u.role === "ADMIN" ? "admin" : "user"}`}>
                    {u.role}
                  </span>
                </td>
                <td>{u.skillLevel || "—"}</td>
                <td>{u.problemsSolved ?? 0}</td>
                <td>{u.currentStreak ?? 0}</td>
                <td>{u.acceptanceRate != null ? `${u.acceptanceRate}%` : "—"}</td>
                <td>{u.algorithmRating ?? "—"}</td>
                <td>{u.createdAt ? new Date(u.createdAt).toLocaleDateString() : "—"}</td>
                <td>
                  <div className="admin-row-actions">
                    <button
                      className="admin-icon-btn"
                      title={u.role === "ADMIN" ? "Demote to USER" : "Promote to ADMIN"}
                      onClick={() => setRoleChangeTarget(u)}
                    >
                      {u.role === "ADMIN" ? <Shield size={15} /> : <ShieldCheck size={15} />}
                    </button>
                    <button
                      className="admin-icon-btn danger"
                      title="Delete user"
                      disabled={currentUser?.id === u.id}
                      onClick={() => setDeleteTarget(u)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && users.length === 0 && (
          <div className="admin-empty-state">No users found.</div>
        )}

        <PaginationBar
          page={page}
          totalPages={totalPages}
          totalElements={totalElements}
          onPageChange={setPage}
          loading={loading}
        />
      </div>

      {/* Delete confirm */}
      {deleteTarget && (
        <ConfirmModal
          title="Delete user?"
          message={`This will permanently delete ${deleteTarget.username}. This cannot be undone.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Role change confirm */}
      {roleChangeTarget && (
        <ConfirmModal
          title={roleChangeTarget.role === "ADMIN" ? "Demote to USER?" : "Promote to ADMIN?"}
          message={`Change ${roleChangeTarget.username}'s role to ${roleChangeTarget.role === "ADMIN" ? "USER" : "ADMIN"}?`}
          confirmLabel="Confirm"
          danger={roleChangeTarget.role !== "ADMIN"}
          onConfirm={() => handleRoleChange(roleChangeTarget.role === "ADMIN" ? "USER" : "ADMIN")}
          onCancel={() => setRoleChangeTarget(null)}
        />
      )}

      {/* Role change log modal */}
      {logOpen && (
        <div className="admin-modal-backdrop" onClick={() => setLogOpen(false)}>
          <div className="admin-log-modal" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3>Role Change Log</h3>
              <button className="admin-modal-close" onClick={() => setLogOpen(false)}><X size={18} /></button>
            </div>
            <div className="admin-log-list">
              {logEntries.length === 0 ? (
                <p className="admin-empty-state">No role changes recorded.</p>
              ) : (
                logEntries.map((entry, idx) => (
                  <div key={idx} className="admin-log-row">
                    <span className="admin-cell-strong">{entry.targetUsername}</span>
                    <span className="admin-log-change">
                      {entry.oldRole} → {entry.newRole}
                    </span>
                    <span className="admin-log-meta">
                      by {entry.changedByAdminUsername} · {new Date(entry.changedAt).toLocaleString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}