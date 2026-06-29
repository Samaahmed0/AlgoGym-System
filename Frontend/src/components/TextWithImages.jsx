import React from 'react';
import MathText from './MathText';

const TextWithImages = ({ text }) => {
    if (!text) return null;

    // Split text into parts: normal text and image URLs
    const parts = text.split(/(\s*https?:\/\/[^\s]+?\.(?:png|jpg|jpeg|gif))/gi);

    return (
        <>
            {parts.map((part, index) => {
                if (/https?:\/\/[^\s]+?\.(?:png|jpg|jpeg|gif)/i.test(part.trim())) {
                    return (
                        <img
                            key={index}
                            src={part.trim()}
                            alt="illustration"
                            style={{ maxWidth: '100%', display: 'block', margin: '10px 0' }}
                        />
                    );
                } else {
                    return <MathText key={index} text={part} />;
                }
            })}
        </>
    );
};

export default TextWithImages;