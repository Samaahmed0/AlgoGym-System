import React from "react";
import { Outlet, useMatch } from "react-router-dom";
import Sidebar from "./Sidebar";
import { UserDataProvider } from "../UserDataContext";
import "../styles/user-app.css";

export default function UserAppLayout() {
  const isCompilerPage = useMatch("/problems/:id");

  return (
    <div className="user-app-shell">
      {!isCompilerPage && <Sidebar />}
      <div className="user-app-main">
        <UserDataProvider>
          <Outlet />
        </UserDataProvider>
      </div>
    </div>
  );
}
