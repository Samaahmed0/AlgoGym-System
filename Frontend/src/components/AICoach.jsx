import React from 'react';
import '../styles/AICoach.css';

const AICoach = ({ aiCoach }) => {
  if (!aiCoach) {
    return null;
  }

  const getErrorTypeIcon = (errorType) => {
    switch(errorType) {
      case 'LOGIC_ERROR': return '🧠';
      case 'SYNTAX_ERROR': return '⚠️';
      case 'RUNTIME_ERROR': return '💥';
      case 'OPTIMIZATION': return '⚡';
      default: return '🤖';
    }
  };

  const getErrorTypeColor = (errorType) => {
    switch(errorType) {
      case 'LOGIC_ERROR': return '#f9d67f';
      case 'SYNTAX_ERROR': return '#ff375f';
      case 'RUNTIME_ERROR': return '#f69bac';
      case 'OPTIMIZATION': return '#61dafb';
      default: return '#aaa';
    }
  };

  return (
    <div className="ai-coach-container">
      <div className="ai-coach-header">
        <span className="ai-icon">🤖</span>
        <span className="ai-title">AlgoBuddy : {aiCoach.errorType.replace(/_/g, ' ')}</span>
        <span 
          className="error-type-badge"
          style={{ background: getErrorTypeColor(aiCoach.errorType) }}
        >
          {getErrorTypeIcon(aiCoach.errorType)}
        </span>
      </div>

      <div className="ai-coach-content">
        <div className="explanation-section">
          <h4>What went wrong?</h4>
          <p>{aiCoach.explanation}</p>
        </div>

        {aiCoach.tips && aiCoach.tips.length > 0 && (
          <div className="tips-section">
            <h4>💡 Tips to fix it:</h4>
            <ul className="tips-list">
              {aiCoach.tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
{/* 
        {aiCoach.suggestedApproach && (
          <div className="approach-section">
            <h4>🎯 Suggested Approach:</h4>
            <p>{aiCoach.suggestedApproach}</p>
          </div>
        )} */}
      </div>
    </div>
  );
};

export default AICoach;