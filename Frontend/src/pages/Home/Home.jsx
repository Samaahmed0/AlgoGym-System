import React from 'react';
import Hero from './Hero';
import WhyChoose from './WhyChoose';
import Footer from './Footer';
import Navbar from './Navbar';
import HowItWorks from './HowItWorks';
import PlatformMetrics from "./PlatformMetrics";
import LearningExperience from "./LearningExperience";
import FinalCTA from "./FinalCTA";


const Home = () => {
    return (
        <>
            <Navbar />
            <Hero />
            <WhyChoose />
            <HowItWorks />
            <PlatformMetrics />
            <LearningExperience />
            <FinalCTA />
            {/* <Footer /> */}
        </>
    );
};

export default Home;