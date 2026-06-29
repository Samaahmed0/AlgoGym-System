import React from 'react';
import '../../styles/Footer.css';
import AlgogymLogo from '../../assets/Algogymlogo.svg'

const Footer = () => {
    return (
        <footer className="footer">
            <div className="footer-container">
                <div className="footer-brand">
                    <div className="footer-logo">
                        <img src={AlgogymLogo} alt="Logo" width="40" height="40" />

                        <span className="logo-text">

                            <span className="text-black">Algo</span>
                            <span className="text-purple">Gym</span></span>

                    </div>
                    <p className="brand-desc">
                        The most advanced platform to practice coding, prepare for interviews, and learn algorithms.
                    </p>
                </div>

                {/* Right Columns: Links */}
                {/* <div className="footer-links">
                    <div className="link-group">
                        <h4>Platform</h4>
                        <ul>
                            <li><a href="#problems">Problems</a></li>
                            <li><a href="#contests">Contests</a></li>
                            <li><a href="#pricing">Pricing</a></li>
                        </ul>
                    </div>
                    <div className="link-group">
                        <h4>Company</h4>
                        <ul>
                            <li><a href="#about">About Us</a></li>
                            <li><a href="#careers">Careers</a></li>
                            <li><a href="#contact">Contact</a></li>
                        </ul>
                    </div>
                </div> */}
            </div>

            <div className="footer-bottom">
                <p>© 2026 AlgoGym. All rights reserved.</p>
            </div>
        </footer>
    );
};

export default Footer;