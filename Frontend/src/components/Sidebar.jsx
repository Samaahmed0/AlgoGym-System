import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import NotificationBell from "./NotificationBell";
import { fetchCurrentUser } from "../api/user.api";
import "../styles/Sidebar.css";
import AlgogymLogo from "../assets/AlgogymLogo.svg"

const icons = {
  Home: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  Dashboard: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
    </svg>
  ),
  Problems: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
    </svg>
  ),
  Recommended: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
      <path d="M5 16l.8 2.4L8 19l-2.2.6L5 22l-.8-2.4L2 19l2.2-.6L5 16z" />
      <path d="M19 14l.6 1.8L21 16l-1.4.2L19 18l-.6-1.8L17 16l1.4-.2L19 14z" />
    </svg>
  ),
  Progress: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" />
    </svg>
  ),
  Profile: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
  ),
  Admin: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  Logout: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
};

const ImpressiveLogo = () => (
  <div className="logo-container">
    <img src={AlgogymLogo} alt="Impressive Logo" width={36} height={36} />
  </div>
);

export default function Sidebar() {
  const menuItems = ["Home", "Dashboard", "Problems", "Recommended", "Progress", "Profile"];
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setIsAdmin(false);
      return;
    }

    fetchCurrentUser()
      .then((user) => setIsAdmin(user?.role === "ADMIN"))
      .catch(() => setIsAdmin(false));
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <ImpressiveLogo />
        <span className="logo-text">

        <span className="text-black">Algo</span>
        <span className="text-purple">Gym</span></span>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item}
            to={item === "Home" ? "/" : `/${item.toLowerCase()}`}
            className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}
          >
            {icons[item]} <span>{item}</span>
          </NavLink>
          
        ))}
        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) => `sidebar-item ${isActive ? "active" : ""}`}
          >
            {icons.Admin} <span>Admin</span>
          </NavLink>
        )}
      </nav>

      <div className="sidebar-footer">
        {localStorage.getItem("token") && (
          <div className="sidebar-notifications">
            <NotificationBell variant="sidebar" />
          </div>
        )}
        <NavLink to="/" className="sidebar-item">
          {icons.Logout} <span>Sign Out</span>
        </NavLink>
      </div>
    </aside>
  );
}