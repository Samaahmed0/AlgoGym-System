import React, { useState } from "react";
import { FiMail } from "react-icons/fi";
import { Link } from "react-router-dom";
import AlgogymLogo from '../assets/Algogymlogo.svg'
import { forgotPassword } from "../api/auth.api";
import "../styles/ForgotPassword.css";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      setError("Please enter your email address");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await forgotPassword(email);
      setSubmitted(true); // always show success — backend never reveals if email exists
    } catch (err) {
      // Only show error for rate limiting, not for missing emails
      setError(err.message || "Something went wrong. Please try again.");
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

        {!submitted ? (
          <>
            <h2>Forgot Password?</h2>
            <p className="subheading">
              Enter your email and we'll send you a reset link.
            </p>

            <form onSubmit={handleSubmit} className="auth-form">
              <label>Email Address</label>
              <div className="input-group">
                <FiMail className="input-icon" />
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>

              {error && <p className="error">{error}</p>}

              <button type="submit" disabled={loading}>
                {loading ? "Sending..." : "Send Reset Link →"}
              </button>
            </form>
          </>
        ) : (
          // Success state — shown regardless of whether email exists (security)
          <div className="success-state">
            <div className="success-icon">✉️</div>
            <h2>Check your inbox</h2>
            <p className="subheading">
              If <strong>{email}</strong> is registered, you'll receive a reset
              link shortly. Check your spam folder too.
            </p>
          </div>
        )}

        <p className="footer">
          Remember your password?{" "}
          <Link to="/login" className="create">Back to Login</Link>
        </p>

      </div>
    </section>
  );
}

export default ForgotPassword;