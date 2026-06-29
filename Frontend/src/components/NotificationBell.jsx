import React, { useEffect, useState, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { Bell, CheckCheck } from "lucide-react";
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "../api/notifications.api";
import "../styles/notifications.css";

const POLL_MS = 60000;

function formatRelativeTime(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}

export default function NotificationBell({ variant = "sidebar", className = "" }) {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const wrapRef = useRef(null);
  const portalPanelRef = useRef(null);
  const [panelPos, setPanelPos] = useState(null);

  const isAuthenticated = !!localStorage.getItem("token");

  const loadUnreadCount = useCallback(() => {
    if (!localStorage.getItem("token")) return Promise.resolve();
    return fetchUnreadCount()
      .then(data => setUnreadCount(data?.count ?? 0))
      .catch(() => {});
  }, []);

  const loadNotifications = useCallback(() => {
    if (!localStorage.getItem("token")) return;
    setLoading(true);
    setError("");
    fetchNotifications()
      .then(data => setNotifications(data ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, POLL_MS);
    return () => clearInterval(interval);
  }, [isAuthenticated, loadUnreadCount]);

  useEffect(() => {
    if (!open || !isAuthenticated) return;
    loadNotifications();
  }, [open, isAuthenticated, loadNotifications]);

  useEffect(() => {
    if (!open || variant !== "sidebar") return undefined;

    const updatePanelPos = () => {
      const btn = wrapRef.current?.querySelector(".notification-bell-btn");
      if (!btn) return;
      const rect = btn.getBoundingClientRect();
      setPanelPos({
        left: rect.right + 12,
        bottom: window.innerHeight - rect.bottom,
      });
    };

    updatePanelPos();
    window.addEventListener("resize", updatePanelPos);
    return () => window.removeEventListener("resize", updatePanelPos);
  }, [open, variant]);

  useEffect(() => {
    if (!open) return undefined;
    const handleClickOutside = (e) => {
      if (wrapRef.current?.contains(e.target)) return;
      if (portalPanelRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const handleMarkRead = async (notification) => {
    if (notification.isRead) return;
    try {
      const updated = await markNotificationRead(notification.id);
      setNotifications(prev =>
        prev.map(n => (n.id === notification.id ? { ...n, ...updated, isRead: true } : n))
      );
      await loadUnreadCount();
    } catch (_) {}
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
      await loadUnreadCount();
    } catch (_) {}
  };

  if (!isAuthenticated) return null;

  const panelContent = (
    <>
      <div className="notification-panel-header">
        <h4>Notifications</h4>
        {unreadCount > 0 && (
          <button type="button" className="notification-mark-all" onClick={handleMarkAllRead}>
            <CheckCheck size={14} /> Mark all read
          </button>
        )}
      </div>

      <div className="notification-panel-body">
        {loading && <p className="notification-panel-status">Loading...</p>}
        {error && <p className="notification-panel-error">{error}</p>}
        {!loading && !error && notifications.length === 0 && (
          <p className="notification-panel-status">No notifications yet.</p>
        )}
        {!loading && notifications.map(n => (
          <button
            key={n.id}
            type="button"
            className={`notification-item ${n.isRead ? "read" : "unread"}`}
            onClick={() => handleMarkRead(n)}
          >
            <div className="notification-item-top">
              <span className="notification-item-title">{n.title}</span>
              {!n.isRead && <span className="notification-unread-dot" aria-label="Unread" />}
            </div>
            <p className="notification-item-message">{n.message}</p>
            <span className="notification-item-time">
              {formatRelativeTime(n.createdAt)}
            </span>
          </button>
        ))}
      </div>
    </>
  );

  return (
    <div
      className={`notification-bell-wrap notification-bell-wrap--${variant} ${className}`}
      ref={wrapRef}
    >
      <button
        type="button"
        className="notification-bell-btn"
        onClick={() => setOpen(v => !v)}
        aria-label="Notifications"
        aria-expanded={open}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="notification-bell-badge">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && variant !== "sidebar" && (
        <div className="notification-panel">{panelContent}</div>
      )}

      {open && variant === "sidebar" && panelPos && createPortal(
        <div
          ref={portalPanelRef}
          className="notification-panel notification-panel--sidebar-portal"
          style={{
            position: "fixed",
            left: panelPos.left,
            bottom: panelPos.bottom,
            top: "auto",
            right: "auto",
          }}
        >
          {panelContent}
        </div>,
        document.body
      )}
    </div>
  );
}
