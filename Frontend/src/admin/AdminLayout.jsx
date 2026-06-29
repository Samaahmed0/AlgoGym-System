import React from "react";
import { Outlet, useNavigate } from "react-router-dom";
import AdminSidebar from "./AdminSidebar";
import { AdminDataProvider } from "./AdminDataContext"; // ← add
import { useAuth } from "../Auth/auth.context";
import "../styles/admin.css";

export default function AdminLayout() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div className="admin-header-left">
          <span className="admin-brand">AlgoGym <span className="admin-brand-accent">Admin</span></span>
        </div>
        <div className="admin-header-right">
          <span className="admin-username">{user?.username || "Admin"}</span>
          <button className="admin-logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="admin-body">
        <AdminSidebar />
        <main className="admin-main-content">
          {/* ← Provider lives here, stays mounted across all /admin/* navigation */}
          <AdminDataProvider>
            <Outlet />
          </AdminDataProvider>
        </main>
      </div>
    </div>
  );
}