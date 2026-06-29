import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { fetchCurrentUserRole } from "../api/admin.api";

export default function ProtectedAdminRoute() {
  const [status, setStatus] = useState("checking"); // checking | ok | denied

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setStatus("denied");
      return;
    }

    fetchCurrentUserRole()
      .then(user => {
        setStatus(user?.role === "ADMIN" ? "ok" : "denied");
      })
      .catch(() => setStatus("denied"));
  }, []);

  if (status === "checking") {
    return (
      <div className="admin-auth-checking">
        <div className="admin-spinner" />
      </div>
    );
  }

  if (status === "denied") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}