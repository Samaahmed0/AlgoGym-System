import React, { useState } from "react";
import { FiUser, FiLock } from "react-icons/fi";
import { Eye, EyeOff } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import AlgogymLogo from '../assets/Algogymlogo.svg'
import { useToast } from "../components/ToastProvider";
import "../styles/Login.css";
import { loginUser } from "../api/auth.api";

function Login() {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      setError("Please fill in all fields");
      return;
    }

    try {
      const data = await loginUser(username, password);
      localStorage.setItem("token", data.token);
      setError("");
      showToast("Logged in successfully!");
      setTimeout(() => navigate("/dashboard"), 1000);
    } catch (err) {
      console.error(err);
      setError("Invalid username or password");
    }
  };

  return (
    <section id="login-page" className="login-page">
      <div className="login-container">
        <div className="logo-section">
          <div className="logo-icon">
           <img src={AlgogymLogo} alt="AlgoGym Logo" width="40" height="40" />
           </div>

          <span className="logo-text">
            <span className="algo">Algo</span>
            <span className="gym">Gym</span>
          </span>
        </div>

        <h2>Welcome Back</h2>
        <p className="subheading">Sign in to continue your training</p>

        <form onSubmit={handleSubmit} className="login-form">
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

          <label>
            Password
            {/* ← Changed from span to Link */}
            <Link to="/forgot-password" className="forgot">Forgot password?</Link>
          </label>
          <div className="input-group password-wrapper">
            <FiLock className="input-icon" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span className="toggle-password" onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </span>
          </div>

          {error && <p className="error">{error}</p>}
          <button type="submit">Log In →</button>
        </form>

        <p className="footer">
          Don't have an account?{" "}
          <Link to="/register" className="create">Create one</Link>
        </p>
      </div>
    </section>
  );
}

export default Login;