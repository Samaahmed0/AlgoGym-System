import { useEffect, useRef } from "react";
import "../../styles/LearningExperience.css";

const experiences = [
  {
    tag: "CONSISTENCY",
    title: "Build the habit, not just the skill",
    body: "AlgoGym's streak system and daily challenges keep you coming back every day. Small, focused sessions compound into deep algorithmic intuition over time.",
    visual: "streak",
  },
  {
    tag: "IMPROVEMENT",
    title: "Watch yourself get sharper",
    body: "Every submission is logged. Your performance graph shows time complexity improvements, solved-per-week trends, and accuracy over time — making progress visible.",
    visual: "graph",
  },
  {
    tag: "FOCUS",
    title: "Know exactly what to fix",
    body: "The analytics engine surfaces your weak topics automatically. If trees trip you up, AlgoGym nudges you toward tree problems — no guessing what to study next.",
    visual: "radar",
  },
];

function StreakVisual() {
  return (
    <div className="le-visual le-visual--streak">
      <div className="le-streak-grid">
        {Array.from({ length: 35 }).map((_, i) => (
          <div
            key={i}
            className={`le-streak-cell ${
              [2,3,5,6,8,9,10,12,13,14,15,16,17,19,20,22,23,24,26,27,28,29,30,31,33,34].includes(i)
                ? "active" : ""
            } ${[28,29,30,31,33,34].includes(i) ? "recent" : ""}`}
            style={{ "--delay": `${i * 28}ms` }}
          />
        ))}
      </div>
      <div className="le-streak-label">
        <span>🔥</span>
        <span>14-day streak</span>
      </div>
    </div>
  );
}

function GraphVisual() {
  const points = [20, 35, 28, 45, 38, 55, 50, 68, 60, 72, 65, 82];
  const max = 90; const w = 280; const h = 120;
  const poly = points.map((v, i) => `${(i / (points.length - 1)) * w},${h - (v / max) * h}`).join(" ");
  const area = `0,${h} ${poly} ${w},${h}`;
  return (
    <div className="le-visual le-visual--graph">
      <svg viewBox={`0 0 ${w} ${h + 10}`} className="le-graph-svg">
        <defs>
          <linearGradient id="gGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5d3fd3" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#5d3fd3" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#gGrad)" />
        <polyline points={poly} fill="none" stroke="#5d3fd3" strokeWidth="2.5"
          strokeLinecap="round" strokeLinejoin="round" className="le-graph-line" />
        {points.map((v, i) => (
          <circle key={i} cx={(i / (points.length - 1)) * w} cy={h - (v / max) * h}
            r={i === points.length - 1 ? 5 : 3}
            fill={i === points.length - 1 ? "#5d3fd3" : "white"}
            stroke="#5d3fd3" strokeWidth="2" />
        ))}
      </svg>
      <div className="le-graph-badge">↑ 41% improvement this month</div>
    </div>
  );
}

function RadarVisual() {
  const topics = ["Arrays", "Trees", "DP", "Graphs", "Sorting", "Strings"];
  const scores = [88, 45, 70, 55, 92, 78];
  const cx = 110; const cy = 110; const r = 80;
  const pt = (angle, radius) => {
    const rad = (angle * Math.PI) / 180;
    return { x: cx + radius * Math.sin(rad), y: cy - radius * Math.cos(rad) };
  };
  const hex = topics.map((_, i) => { const p = pt((360/6)*i, r); return `${p.x},${p.y}`; }).join(" ");
  const data = scores.map((s, i) => { const p = pt((360/6)*i, (s/100)*r); return `${p.x},${p.y}`; }).join(" ");
  return (
    <div className="le-visual le-visual--radar">
      <svg viewBox="0 0 220 220" className="le-radar-svg">
        <defs>
          <linearGradient id="rGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#5d3fd3" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.15" />
          </linearGradient>
        </defs>
        {[0.25,0.5,0.75,1].map(s => (
          <polygon key={s} points={topics.map((_,i)=>{const p=pt((360/6)*i,r*s);return`${p.x},${p.y}`;}).join(" ")}
            fill="none" stroke="#e5e7eb" strokeWidth="1" />
        ))}
        {topics.map((_,i)=>{const p=pt((360/6)*i,r);return<line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="#e5e7eb" strokeWidth="1"/>;} )}
        <polygon points={data} fill="url(#rGrad)" stroke="#5d3fd3" strokeWidth="2" />
        {topics.map((t,i)=>{const p=pt((360/6)*i,r+16);return<text key={i} x={p.x} y={p.y} textAnchor="middle" dominantBaseline="middle" fontSize="9" fill="#6b7280" fontWeight="600">{t}</text>;})}
      </svg>
      <div className="le-radar-badge">Weak spot: Trees → 3 new problems queued</div>
    </div>
  );
}

const visuals = { streak: StreakVisual, graph: GraphVisual, radar: RadarVisual };

export default function LearningExperience() {
  const rowRefs = useRef([]);
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => e.isIntersecting && e.target.classList.add("le-row-visible")),
      { threshold: 0.15 }
    );
    rowRefs.current.forEach(el => el && obs.observe(el));
    return () => obs.disconnect();
  }, []);

  return (
    <section className="le-section" id="experience">
      <div className="le-header">
        <span className="le-pill">THE EXPERIENCE</span>
        <h2 className="le-title">Practice that actually <em>sticks</em></h2>
        <p className="le-subtitle">
          AlgoGym isn't a problem bank. It's a deliberate practice environment built around how humans actually improve.
        </p>
      </div>
      <div className="le-rows">
        {experiences.map((exp, i) => {
          const Visual = visuals[exp.visual];
          return (
            <div key={exp.tag} className={`le-row le-row--${i % 2 === 0 ? "normal" : "reversed"}`}
              ref={el => (rowRefs.current[i] = el)} style={{ "--row-delay": `${i * 80}ms` }}>
              <div className="le-row-text">
                <span className="le-row-tag">{exp.tag}</span>
                <h3 className="le-row-title">{exp.title}</h3>
                <p className="le-row-body">{exp.body}</p>
              </div>
              <div className="le-row-visual"><Visual /></div>
            </div>
          );
        })}
      </div>
    </section>
  );
}