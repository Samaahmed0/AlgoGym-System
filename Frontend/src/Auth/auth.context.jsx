import React, { createContext, useContext } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Later this comes from JWT / session
  const user = {
    id: "stu_123",
    name: "Alex"
  };

  return (
    <AuthContext.Provider value={{ user }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
