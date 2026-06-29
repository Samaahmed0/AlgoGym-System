import React from 'react';
import "../../styles/WhyChoose.css";
import AlgogymLogo from "../../assets/AlgogymLogo.svg"
const features = [
    {
        title: "AI-Powered Recommendations",
        desc: "Our system learns your weak spots and suggests problems that target them specifically.",
        icon: <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="5" y="5" width="14" height="14" rx="2" stroke="#A855F7" stroke-width="2" />
            <rect x="9" y="9" width="6" height="6" rx="1" fill="#A855F7" fill-opacity="0.2" stroke="#A855F7" stroke-width="1.5" />
            <path d="M9 2V5M12 2V5M15 2V5" stroke="#A855F7" stroke-width="1.5" stroke-linecap="round" />
            <path d="M9 19V22M12 19V22M15 19V22" stroke="#A855F7" stroke-width="1.5" stroke-linecap="round" />
            <path d="M2 9H5M2 12H5M2 15H5" stroke="#A855F7" stroke-width="1.5" stroke-linecap="round" />
            <path d="M19 9H22M19 12H22M19 15H22" stroke="#A855F7" stroke-width="1.5" stroke-linecap="round" />
        </svg>
    },
    {
        title: "Built-in Compiler",
        desc: "Write, run, and debug code in 60+ languages directly in your browser.",
        icon: <img src={AlgogymLogo} alt="Impressive Logo" width={36} height={36} />
    },
    {
        title: "Deep Analytics",
        desc: "Visualize your progress with detailed charts. Track time complexity and accuracy.",
        icon: <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 20H21" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" />
            <path d="M7 16V10" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" />
            <path d="M12 16V4" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" />
            <path d="M17 16V14" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" />
            <rect x="2" y="2" width="20" height="20" rx="5" stroke="#3B82F6" stroke-width="1" stroke-opacity="0.2" />
        </svg>
    }
];

const WhyChoose = () => {
    return (
        <section id="why-algogym" className="why-choose-section">

            <div className="container">
                <div className='BG'>
                    <h1 className="section-title">Why Choose <em>AlgoGym</em>?</h1>
                    <p className="section-subtitle">We've built the ultimate environment for you to master data structures and algorithms.</p>
                </div>
                <div className="feature-grid">
                    {features.map((item, index) => (
                        <div key={index} className="feature-card">
                            <div className="icon-box">{item.icon}</div>
                            <h3>{item.title}</h3>
                            <p>{item.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default WhyChoose;
