import React from "react";

const STATUS_STYLES = {
  ONLINE:   { color: "#10b981", label: "Online" },
  DEGRADED: { color: "#f59e0b", label: "Degraded" },
  OFFLINE:  { color: "#ef4444", label: "Offline" },
};

export default function HealthBadge({ name, status, latencyMs }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.OFFLINE;

  return (
    <div className="health-badge-row">
      <div className="health-badge-left">
        <span className="health-dot" style={{ background: style.color, boxShadow: `0 0 8px ${style.color}` }} />
        <span className="health-name">{name}</span>
      </div>
      <div className="health-badge-right">
        <span className="health-status" style={{ color: style.color }}>{style.label}</span>
        {latencyMs != null && <span className="health-latency">{latencyMs}ms</span>}
      </div>
    </div>
  );
}