import { useEffect, useRef } from "react";
import "../../styles/HowItWorks.css";

const steps = [
  {
    number: "01",
    title: "Choose a Problem",
    description: "Browse 3,000+ challenges filtered by topic, difficulty, or tag.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
  },
  {
    number: "02",
    title: "Write & Run Code",
    description: "Built-in compiler. No setup, just code.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
  },
  {
    number: "03",
    title: "Get AI Hints",
    description: "Ask the AI coach for a nudge or a full walkthrough anytime.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    number: "04",
    title: "Track Progress",
    description: "See your improvement with deep analytics and smart insights.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-3 3" />
      </svg>
    ),
  },
];

export default function HowItWorks() {
  const sectionRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => e.isIntersecting && e.target.classList.add("hiw-visible"));
      },
      { threshold: 0.1 }
    );
    sectionRef.current?.querySelectorAll(".hiw-step").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section className="hiw-section" id="how-it-works" ref={sectionRef}>
      <div className="hiw-header">
        <span className="hiw-label">THE WORKFLOW</span>
        <h2 className="hiw-title">
          From zero to <em>solved</em> in four steps
        </h2>
        <p className="hiw-subtitle">A focused loop that turns every session into real progress.</p>
      </div>

      <div className="hiw-grid">
        {steps.map((step, i) => (
          <div className="hiw-step" key={step.number} style={{ "--delay": `${i * 110}ms` }}>
            {/* connector arrow between steps */}
            {i < steps.length - 1 && (
              <div className="hiw-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
            <div className="hiw-icon-wrap">{step.icon}</div>
            <span className="hiw-num">{step.number}</span>
            <h3 className="hiw-card-title">{step.title}</h3>
            <p className="hiw-card-desc">{step.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}