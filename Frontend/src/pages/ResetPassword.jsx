import React, { useState } from "react";
import { FiLock } from "react-icons/fi";
import { Eye, EyeOff } from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AlgogymLogo from '../assets/Algogymlogo.svg'
import { resetPassword } from "../api/auth.api";
import { useToast } from "../components/ToastProvider";
import "../styles/ForgotPassword.css";

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token"); // reads ?token=xxx from the email link
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // If no token in URL, show invalid state
  if (!token) {
    return (
      <section className="auth-page">
        <div className="auth-container">
          <div className="success-state">
            <div className="success-icon">⚠️</div>
            <h2>Invalid Link</h2>
            <p className="subheading">
              This password reset link is invalid or has expired.
              Please request a new one.
            </p>
          </div>
          <p className="footer">
            <Link to="/forgot-password" className="create">Request new link</Link>
          </p>
        </div>
      </section>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!newPassword || !confirmPassword) {
      setError("Please fill in all fields");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, newPassword);
      showToast("Password reset successfully!");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err.message || "Reset failed. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-container">

        {/* Logo */}
        <div className="logo-section">
          <div className="logo-icon">
          <img src={AlgogymLogo} alt="AlgoGym Logo" width="40" height="40" />
          </div>
          <span className="logo-text">
            <span className="algo">Algo</span>
            <span className="gym">Gym</span>
          </span>
        </div>

        <h2>Reset Password</h2>
        <p className="subheading">Choose a strong new password for your account.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>New Password</label>
          <div className="input-group password-wrapper">
            <FiLock className="input-icon" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={loading}
            />
            <span
              className="toggle-password"
              onClick={() => setShowPassword(p => !p)}
              style={{ position: "absolute", right: 16, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "#9ca3af" }}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </span>
          </div>

          <label>Confirm Password</label>
          <div className="input-group password-wrapper">
            <FiLock className="input-icon" />
            <input
              type={showConfirm ? "text" : "password"}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
            />
            <span
              className="toggle-password"
              onClick={() => setShowConfirm(p => !p)}
              style={{ position: "absolute", right: 16, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "#9ca3af" }}
            >
              {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
            </span>
          </div>

          {/* Password requirements hint */}
          <p className="requirements-hint">
            Must be 8+ characters with uppercase, lowercase, number and special character.
          </p>

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? "Resetting..." : "Reset Password →"}
          </button>
        </form>

        <p className="footer">
          <Link to="/login" className="create">Back to Login</Link>
        </p>

      </div>
    </section>
  );
}

export default ResetPassword;