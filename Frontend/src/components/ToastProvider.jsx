import React, { createContext, useContext, useState } from "react";

const ToastContext = createContext();

export function useToast() {
  return useContext(ToastContext);
}

export default function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  const showToast = (msg) => {
    setToast(msg);
    // Automatically hide after 2 seconds
    setTimeout(() => setToast(null), 2000);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      {/* Only render toast if there’s a message */}
      {toast && (
        <div 
          className="toast" 
          style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            backgroundColor: "#5d3ebc",
            color: "white",
            padding: "10px 18px",
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            zIndex: 9999,
            fontWeight: 500,
            animation: "fadeInOut 2s forwards"
          }}
        >
          {toast}
        </div>
      )}

      <style>
        {`
          @keyframes fadeInOut {
            0% { opacity: 0; transform: translateY(10px); }
            10% { opacity: 1; transform: translateY(0); }
            90% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(10px); }
          }
        `}
      </style>
    </ToastContext.Provider>
  );
}