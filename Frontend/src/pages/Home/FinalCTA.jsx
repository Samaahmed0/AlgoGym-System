import { Link } from "react-router-dom";
import "../../styles/FinalCTA.css";

export default function FinalCTA() {
  return (
    <section className="fcta-section">
      <div className="fcta-bg-blob fcta-bg-blob--left" />
      <div className="fcta-bg-blob fcta-bg-blob--right" />

      <div className="fcta-inner">

        <h2 className="fcta-title">
          Ready to level up your
          <br />
          <span className="fcta-title-highlight">problem solving?</span>
        </h2>

        <p className="fcta-sub">
          Join engineers who practice smarter — not just harder.
          <br />
          Your first session takes 60 seconds to start.
        </p>

        <div className="fcta-actions">
          <Link to="/register" className="fcta-btn-primary">
            Start Solving Now
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>

      </div>
    </section>
  );
}