import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, FileCode2, ListChecks,
  BarChart3, Tags, Sparkles, Bell, Settings, ArrowLeft
} from "lucide-react";
import "../styles/admin.css";

const NAV_ITEMS = [
  { to: "/admin/overview", label: "Overview", icon: LayoutDashboard },
  { to: "/admin/users", label: "Users", icon: Users },
  { to: "/admin/problems", label: "Problems", icon: FileCode2 },
  { to: "/admin/submissions", label: "Submissions", icon: ListChecks },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/admin/tags", label: "Tags", icon: Tags },
  { to: "/admin/ai-feedback", label: "AI Feedback", icon: Sparkles },
  { to: "/admin/notifications", label: "Notifications", icon: Bell },
  { to: "/admin/settings", label: "Settings", icon: Settings },
];

export default function AdminSidebar() {
  return (
    <nav className="admin-sidebar">
      <div className="admin-sidebar-nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `admin-sidebar-item ${isActive ? "active" : ""}`}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>

      <div className="admin-sidebar-footer">
        <NavLink to="/dashboard" className="admin-sidebar-item admin-sidebar-exit">
          <ArrowLeft size={18} />
          <span>Back to App</span>
        </NavLink>
      </div>
    </nav>
  );
}