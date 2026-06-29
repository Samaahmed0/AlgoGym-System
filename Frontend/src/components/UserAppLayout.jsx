import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import { UserDataProvider } from "../UserDataContext";
import "../styles/user-app.css";

export default function UserAppLayout() {
  return (
    <div className="user-app-shell">
      <Sidebar />
      <div className="user-app-main">
        <UserDataProvider>
          <Outlet />
        </UserDataProvider>
      </div>
    </div>
  );
}
