import React from "react";

const VERDICT_STYLES = {
  ACCEPTED:              { color: "#16a34a", bg: "#dcfce7", label: "Accepted" },
  WRONG_ANSWER:          { color: "#dc2626", bg: "#fee2e2", label: "Wrong Answer" },
  COMPILATION_ERROR:     { color: "#ea580c", bg: "#ffedd5", label: "Compile Error" },
  RUNTIME_ERROR:         { color: "#ca8a04", bg: "#fef9c3", label: "Runtime Error" },
  TIME_LIMIT_EXCEEDED:   { color: "#9333ea", bg: "#f3e8ff", label: "TLE" },
  MEMORY_LIMIT_EXCEEDED: { color: "#2563eb", bg: "#dbeafe", label: "MLE" },
};

export default function VerdictBadge({ verdict }) {
  const style = VERDICT_STYLES[verdict] || { color: "#64748b", bg: "#f1f5f9", label: verdict || "Unknown" };
  return (
    <span className="verdict-badge" style={{ color: style.color, background: style.bg }}>
      {style.label}
    </span>
  );
}