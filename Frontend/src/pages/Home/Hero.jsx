import React from 'react';
import '../../styles/Hero.css';
import { useNavigate } from "react-router-dom";

const Hero = () => {
  const navigate = useNavigate();

  return (
    <div className="hero_container">
      <div className="hero_content">
        <h1>
          Train Your <br />
          <span className="algo">Algorithms.</span> <br />
          Grow Smarter.
        </h1>
        <p>
          Master coding challenges with our intelligent platform. Get personalized
          problem recommendations, AI-driven explanations, and track your growth in realtime.
        </p>
        <div className="hero_btns">
          <button className="start_training_btn" onClick={() => navigate("/register")}>
            Start Training Now →
          </button>
          <button className="explore_problems_btn" onClick={() => navigate("/problems")}>
            Explore Problems
          </button>
        </div>
      </div>

      {/* Animated code visual */}
      <div className="hero_visual">
        <div className="hv_window">
          <div className="hv_titlebar">
            <span className="hv_dot hv_dot--red" />
            <span className="hv_dot hv_dot--yellow" />
            <span className="hv_dot hv_dot--green" />
            <span className="hv_filename">two_sum.py</span>
          </div>
          <div className="hv_body">
            <pre className="hv_code">
              <span className="hv_line hv_line--1">
                <span className="hv_kw">def</span> <span className="hv_fn">twoSum</span>
                <span className="hv_pun">(</span>nums<span className="hv_pun">,</span> target<span className="hv_pun">):</span>
              </span>
              <span className="hv_line hv_line--2">
                {"    "}seen <span className="hv_op">=</span> <span className="hv_pun">{"{}"}</span>
              </span>
              <span className="hv_line hv_line--3">
                {"    "}<span className="hv_kw">for</span> i<span className="hv_pun">,</span> n <span className="hv_kw">in</span> <span className="hv_fn">enumerate</span><span className="hv_pun">(</span>nums<span className="hv_pun">):</span>
              </span>
              <span className="hv_line hv_line--4 hv_line--active">
                {"        "}diff <span className="hv_op">=</span> target <span className="hv_op">-</span> n
              </span>
              <span className="hv_line hv_line--5">
                {"        "}<span className="hv_kw">if</span> diff <span className="hv_kw">in</span> seen<span className="hv_pun">:</span>
              </span>
              <span className="hv_line hv_line--6">
                {"            "}<span className="hv_kw">return</span> <span className="hv_pun">[</span>seen<span className="hv_pun">[</span>diff<span className="hv_pun">],</span> i<span className="hv_pun">]</span>
              </span>
              <span className="hv_line hv_line--7">
                {"        "}seen<span className="hv_pun">[</span>n<span className="hv_pun">]</span> <span className="hv_op">=</span> i
              </span>
              <span className="hv_cursor" />
            </pre>
          </div>
          <div className="hv_footer">
            <div className="hv_result">
              <span className="hv_result_dot" />
              <span className="hv_result_text">All test cases passed</span>
            </div>
            <div className="hv_badges">
              <span className="hv_badge hv_badge--easy">Easy</span>
              <span className="hv_badge hv_badge--time">O(n)</span>
            </div>
          </div>
        </div>

        {/* Floating cards */}
        <div className="hv_float hv_float--ai">
          <div className="hv_float_icon">✦</div>
          <div>
            <div className="hv_float_title">AI Hint</div>
            <div className="hv_float_sub">Use a hash map for O(n)</div>
          </div>
        </div>

        <div className="hv_float hv_float--streak">
          <div className="hv_float_flame">🔥</div>
          <div>
            <div className="hv_float_num">14</div>
            <div className="hv_float_sub">day streak</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;