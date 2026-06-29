import React from "react";
import "../../styles/admin.css";

export default function StatCard({ icon, label, value, accent }) {
  return (
    <div className="stat-card-admin">
      <div className="stat-card-icon" style={{ background: `${accent}15`, color: accent }}>
        {icon}
      </div>
      <div className="stat-card-text">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-value">{value}</span>
      </div>
    </div>
  );
}