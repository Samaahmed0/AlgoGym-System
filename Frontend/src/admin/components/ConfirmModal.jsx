import React from "react";
import { AlertTriangle, X } from "lucide-react";
import "../../styles/admin.css";

export default function ConfirmModal({ title, message, confirmLabel = "Confirm", danger = true, onConfirm, onCancel }) {
  return (
    <div className="admin-modal-backdrop" onClick={onCancel}>
      <div className="admin-confirm-modal" onClick={e => e.stopPropagation()}>
        <button className="admin-modal-close" onClick={onCancel}><X size={18} /></button>
        <div className="admin-confirm-icon" style={{ color: danger ? "#ef4444" : "#6366f1" }}>
          <AlertTriangle size={28} />
        </div>
        <h3 className="admin-confirm-title">{title}</h3>
        <p className="admin-confirm-message">{message}</p>
        <div className="admin-confirm-actions">
          <button className="admin-btn-secondary" onClick={onCancel}>Cancel</button>
          <button
            className={danger ? "admin-btn-danger" : "admin-btn-primary"}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}