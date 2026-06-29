import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import '../../styles/Navbar.css';
import AlgogymLogo from '../../assets/Algogymlogo.svg'

const Navbar = () => {
    const location = useLocation();
    // Check if we are currently on the Home page
    const isHomePage = location.pathname === "/";

    return (
        <div>
            <div className="navbar">
                <Link
                    to="/"
                    className="nav-logo"
                    style={{ textDecoration: "none", display: "flex", alignItems: "center" }}>
                    <img src={AlgogymLogo} alt="Logo" width="40" height="40" />
                    <h2 className="logo-text">
                        <span className="text-black">Algo</span>
                        <span className="text-purple">Gym</span>
                    </h2>
                </Link>


                {isHomePage && (
                    <>
                        <div className="links">
                            <ul>

                                <li>
                                    <a href="#why-algogym" >Features</a>
                                </li>
                                <li>
                                    <a href="#how-it-works" >How it Works</a>
                                </li>

                            </ul>
                        </div>
                        <div className="btn">
                            <Link to="/login" className="btn-link">
                                Log In
                            </Link>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Navbar;