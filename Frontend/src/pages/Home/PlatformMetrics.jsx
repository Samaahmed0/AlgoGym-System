import { useEffect, useRef, useState } from "react";
import "../../styles/PlatformMetrics.css";

const metrics = [
  { value: 3000, suffix: "+", label: "Problems", description: "Across all difficulty levels" },
  { value: 60, suffix: "+", label: "Languages", description: "From Python to Rust" },
  { value: null, display: "∞", suffix: "", label: "Algorithm Topics", description: "Arrays, DP, Graphs & more" },
  { value: null, display: "AI", suffix: "", label: "Powered Assistance", description: "Hints, explanations & coaching" },
];

function useCountUp(target, duration = 1400, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start || target === null) return;
    let startTime = null;
    const step = (ts) => {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [start, target, duration]);
  return count;
}

function MetricItem({ value, display, suffix, label, description, started, index }) {
  const count = useCountUp(value, 1400, started);

  return (
    <div className="pm-item" style={{ "--i": index }}>
      <div className="pm-number">
        <span className="pm-count">
          {display ? display : started ? count : 0}
        </span>
        <span className="pm-suffix">{suffix}</span>
      </div>
      <div className="pm-label">{label}</div>
      <div className="pm-desc">{description}</div>
    </div>
  );
}

export default function PlatformMetrics() {
  const [started, setStarted] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setStarted(true); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="pm-section" ref={ref}>
      <div className="pm-inner">
        <div className="pm-eyebrow">BY THE NUMBERS</div>
        <div className="pm-grid">
          {metrics.map((m, i) => (
            <MetricItem key={m.label} {...m} started={started} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}