import React, { useState } from "react";
import "../styles/Register.css";
import { FiMail, FiLock, FiUser } from "react-icons/fi";
import { Eye, EyeOff } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth.api";

function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ✅ Professional password requirement checks
  const passwordChecks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };

  const isPasswordValid =
    passwordChecks.length &&
    passwordChecks.uppercase &&
    passwordChecks.number &&
    passwordChecks.special;


const handleSubmit = async (e) => {
  e.preventDefault();

  if (username === "" || email === "" || password === "") {
    setError("Please fill in all fields");
    setSuccess("");
    return;
  }

  if (!isPasswordValid) {
    setError("Please meet all password requirements");
    setSuccess("");
    return;
  }

  try {
    setError("");
    setSuccess("");

    const data = await registerUser({
      username,
      email,
      password,
      skillLevel: "beginner", // 👈 important (you can change later)
    });

    console.log("Registered:", data);

    setSuccess("Account created successfully!");

    setTimeout(() => {
      navigate("/login");
    }, 1500);

  } catch (err) {
    console.error(err);
    setError(err.message || "Registration failed");
    setSuccess("");
  }
};

  return (
    <div className="login-page">
      <div className="login-container">
        {/* Logo */}
          <div className="logo-section">
            <div className="logo-icon">
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect width="24" height="24" rx="6" fill="url(#grad1)" />
              <path
                d="M7 8L4 12L7 16"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
             />
             <path
                d="M17 8L20 12L17 16"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
             <line
                x1="9"
                y1="12"
                x2="15"
                y2="12"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <circle cx="12" cy="12" r="1.5" fill="white" />
              <defs>
                <linearGradient
                  id="grad1"
                  x1="0"
                  y1="0"
                  x2="24"
                  y2="24"
                  gradientUnits="userSpaceOnUse"
                 >
                  <stop stopColor="#6366F1" />
                  <stop offset="1" stopColor="#A855F7" />
                </linearGradient>
              </defs>
            </svg>
            </div>

          <span className="logo-text">
            <span className="algo">Algo</span>
            <span className="gym">Gym</span>
          </span>
        </div>

        {/* Heading */}
        <h2>Create Account</h2>
        <p className="subheading">Start your coding journey today</p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          {/* Username */}
          <label>Username</label>
          <div className="input-group">
            <FiUser className="input-icon" />
            <input
              type="text"
              placeholder="john_doe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          {/* Email */}
          <label>Email Address</label>
          <div className="input-group">
            <FiMail className="input-icon" />
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {/* Password */}
          <label>Password</label>
          <div className="input-group password-wrapper">
            <FiLock className="input-icon" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span
              className="toggle-password"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </span>
          </div>

          {/* ✅ Professional Live Checklist */}
          {password && (
            <div className="password-checklist">
              <p className={passwordChecks.length ? "valid" : "invalid"}>
                {passwordChecks.length ? "✔" : "✖"} At least 8 characters
              </p>
              <p className={passwordChecks.uppercase ? "valid" : "invalid"}>
                {passwordChecks.uppercase ? "✔" : "✖"} One uppercase letter
              </p>
              <p className={passwordChecks.number ? "valid" : "invalid"}>
                {passwordChecks.number ? "✔" : "✖"} One number
              </p>
              <p className={passwordChecks.special ? "valid" : "invalid"}>
                {passwordChecks.special ? "✔" : "✖"} One special character
              </p>
            </div>
          )}

          {/* Error message */}
          {error && <p className="error">{error}</p>}

          {/* Success message */}
          {success && <p className="success">{success}</p>}

          {/* Register button */}
          <button type="submit">Create Account →</button>
        </form>

        {/* Footer */}
        <p className="footer">
          Already have an account?{" "}
          <Link to="/login" className="create">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Register;