import React, { useEffect, useState, useCallback } from "react";
import { Bell, Send, Megaphone, User } from "lucide-react";
import { createAdminNotification } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext";
import "../../styles/admin.css";

const TYPE_OPTIONS = ["ANNOUNCEMENT", "SYSTEM", "MAINTENANCE", "UPDATE"];

export default function AdminNotifications() {
  const { getBroadcastNotifications, invalidateBroadcasts, broadcastsVersion } = useAdminData();

  const [broadcasts, setBroadcasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [target, setTarget] = useState("broadcast");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState("ANNOUNCEMENT");
  const [userId, setUserId] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [sendSuccess, setSendSuccess] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    getBroadcastNotifications()
      .then(data => {
        setBroadcasts(data);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [getBroadcastNotifications, broadcastsVersion]);

  useEffect(() => { load(); }, [load]);

  const handleSend = async (e) => {
    e.preventDefault();
    setSendError("");
    setSendSuccess("");

    const trimmedTitle = title.trim();
    const trimmedMessage = message.trim();
    const trimmedUserId = userId.trim();

    if (!trimmedTitle) {
      setSendError("Title is required");
      return;
    }
    if (!trimmedMessage) {
      setSendError("Message is required");
      return;
    }
    if (target === "personal" && !trimmedUserId) {
      setSendError("User ID is required for personal notifications");
      return;
    }

    const body = {
      title: trimmedTitle,
      message: trimmedMessage,
      type,
    };
    if (target === "personal") {
      body.userId = trimmedUserId;
    }

    setSending(true);
    try {
      await createAdminNotification(body);
      setTitle("");
      setMessage("");
      setUserId("");
      setType("ANNOUNCEMENT");
      setTarget("broadcast");
      if (target === "broadcast") {
        invalidateBroadcasts();
      }
      setSendSuccess(
        target === "broadcast"
          ? "Broadcast sent to all users."
          : `Personal notification sent to user ${trimmedUserId}.`
      );
      setTimeout(() => setSendSuccess(""), 4000);
    } catch (err) {
      setSendError(err.message || "Failed to send notification");
    } finally {
      setSending(false);
    }
  };

  if (error && broadcasts.length === 0 && !loading) {
    return <div className="admin-error-state">Failed to load notifications: {error}</div>;
  }

  return (
    <div className="admin-notifications-page">
      <h1 className="admin-page-title">Notifications</h1>

      <div className="admin-form-card">
        <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Send size={16} /> Send Notification
        </h3>

        <div className="admin-segmented" style={{ marginBottom: 20 }}>
          <button
            type="button"
            className={`admin-segmented-btn ${target === "broadcast" ? "active" : ""}`}
            onClick={() => setTarget("broadcast")}
          >
            <Megaphone size={13} style={{ marginRight: 4 }} /> Broadcast
          </button>
          <button
            type="button"
            className={`admin-segmented-btn ${target === "personal" ? "active" : ""}`}
            onClick={() => setTarget("personal")}
          >
            <User size={13} style={{ marginRight: 4 }} /> Personal
          </button>
        </div>

        <form onSubmit={handleSend} className="admin-notification-form">
          <div className="admin-form-row">
            <label className="admin-form-label">Title</label>
            <input
              className="admin-rename-input"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Notification title"
              style={{ cursor: "text" }}
            />
          </div>

          <div className="admin-form-row">
            <label className="admin-form-label">Message</label>
            <textarea
              className="admin-textarea"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Notification message"
              rows={4}
              style={{ cursor: "text" }}
            />
          </div>

          <div className="admin-form-row admin-form-row-inline">
            <div className="admin-form-field">
              <label className="admin-form-label">Type</label>
              <select className="admin-select" value={type} onChange={e => setType(e.target.value)}>
                {TYPE_OPTIONS.map(t => (
                  <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>

            {target === "personal" && (
              <div className="admin-form-field">
                <label className="admin-form-label">User ID</label>
                <input
                  className="admin-rename-input"
                  value={userId}
                  onChange={e => setUserId(e.target.value)}
                  placeholder="Target user ID"
                  style={{ cursor: "text" }}
                />
              </div>
            )}
          </div>

          {sendError && <p className="admin-inline-error">{sendError}</p>}
          {sendSuccess && <div className="admin-success-banner">{sendSuccess}</div>}

          <button type="submit" className="admin-btn-primary" disabled={sending} style={{ marginTop: 16 }}>
            {sending ? "Sending..." : target === "broadcast" ? "Broadcast to All Users" : "Send to User"}
          </button>
        </form>
      </div>

      {error && <div className="admin-error-state" style={{ height: "auto", marginBottom: 16 }}>{error}</div>}

      <div className={`admin-table-card ${loading ? "admin-table-updating" : ""}`}>
        <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8, padding: "18px 18px 0" }}>
          <Bell size={16} /> Broadcast History
        </h3>
        <table className="admin-data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Message</th>
              <th>Type</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {broadcasts.map(n => (
              <tr key={n.id}>
                <td className="admin-cell-mono">{n.id}</td>
                <td className="admin-cell-strong">{n.title}</td>
                <td className="admin-ai-feedback-excerpt">{n.message}</td>
                <td>
                  <span className="admin-tag-chip-lg">
                    <Megaphone size={12} /> {n.type?.replace(/_/g, " ") ?? "—"}
                  </span>
                </td>
                <td>{n.createdAt ? new Date(n.createdAt).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && broadcasts.length === 0 && (
          <div className="admin-empty-state">No broadcast notifications yet.</div>
        )}
      </div>
    </div>
  );
}
