import React, { useState, useEffect } from 'react';
import ProblemPanel from '../components/ProblemPanel';
import CodeEditor from '../components/CodeEditor';
import Console from '../components/Console';
import AICoach from '../components/AICoach';
import "../styles/ProblemCompilerPage.css"
import { useParams } from "react-router-dom";
import { useUserData } from '../UserDataContext';

const API_BASE = 'http://localhost:8080/api';

function ProblemCompilerPage() {
  const { id } = useParams();
  const { invalidateRecommendations, recordSubmissionActivity } = useUserData();
  const [problem, setProblem] = useState(null);
  const [problemLoading, setProblemLoading] = useState(true);
  const [problemError, setProblemError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [activeTab, setActiveTab] = useState('console');

  useEffect(() => {
    setProblemLoading(true);
    setProblemError(null);

    fetch(`${API_BASE}/problems/${id}`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Problem not found: ${res.status}`);
        }
        return res.json();
      })
      .then(data => { 
        setProblem(data); 
        setProblemLoading(false); 
      })
      .catch(err => { 
        console.error('Error loading problem:', err);
        setProblemError(err.message); 
        setProblemLoading(false); 
      });
  }, [id]);

  const handleRunCode = async (code, languageId, languageName) => {
      setIsRunning(true);
      setResult(null);
      setActiveTab('console');

      try {
          const token = localStorage.getItem('token'); // or wherever you store it
          const res = await fetch(`${API_BASE}/code/run`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                  problemId: problem.id,
                  sourceCode: code,
                  languageId,
                  languageName
              }),
          });

          if (!res.ok) throw new Error('Run failed');
          const data = await res.json();
          setResult({ ...data, type: 'run' });
      } catch (err) {
          console.error('Run error:', err);
          setResult({ error: err.message, type: 'error' });
      } finally {
          setIsRunning(false);
      }
  };

  const handleSubmitCode = async (code, languageId, languageName) => {
      setIsSubmitting(true);
      setResult(null);
      setActiveTab('console');

      try {
          const token = localStorage.getItem('token'); // or wherever you store it
          const res = await fetch(`${API_BASE}/code/submit`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                  problemId: problem.id,
                  sourceCode: code,
                  languageId,
                  languageName
              }),
          });

          if (!res.ok) throw new Error('Submit failed');
          const data = await res.json();
          setResult({ ...data, type: 'submit' });
          setSubmissions(prev => [data, ...prev]);
          await recordSubmissionActivity(data, problem, languageName);
          if (data.verdict === 'ACCEPTED') {
            invalidateRecommendations();
          }
      } catch (err) {
          console.error('Submit error:', err);
          setResult({ error: err.message, type: 'error' });
      } finally {
          setIsSubmitting(false);
      }
  };

  if (problemLoading) return (
    <div className="loading">
      <div className="modern-spinner"></div>
      <p>Loading problem...</p>
    </div>
  );
  
  if (problemError) return (
    <div className="error">
      <p>Error: {problemError}</p>
      <button onClick={() => window.location.reload()}>Retry</button>
    </div>
  );

  const hasAICoach = result?.aiExplanation != null;

  return (
    <div className="app-container">
      <div className="left-panel">
        <ProblemPanel problem={problem} submissions={submissions} />
      </div>
      <div className="right-panel">
        <div className="editor-section">
          <CodeEditor
            onRunCode={handleRunCode}
            onSubmitCode={handleSubmitCode}
            isRunning={isRunning || isSubmitting}
          />
        </div>

        <div className="bottom-panel">
          <div className="bottom-tabs">
            <button
              className={`bottom-tab ${activeTab === 'console' ? 'active' : ''}`}
              onClick={() => setActiveTab('console')}
            >
              Console
              {result && (
                <span className={`tab-dot ${
                  result.verdict === 'ACCEPTED' ? 'dot-success' :
                  result.verdict === 'TIME_LIMIT_EXCEEDED' ? 'dot-warning' : 'dot-error'
                }`} />
              )}
            </button>

            {hasAICoach && (
              <button
                className={`bottom-tab ${activeTab === 'aicoach' ? 'active' : ''} ai-tab`}
                onClick={() => setActiveTab('aicoach')}
              >
                🤖 AI Coach
                <span className="tab-dot dot-ai" />
              </button>
            )}
          </div>

          <div className="bottom-content">
            {activeTab === 'console' && <Console result={result} />}
            {activeTab === 'aicoach' && hasAICoach && (
              <AICoach aiCoach={{
                errorType: result.aiErrorType,
                explanation: result.aiExplanation,
                tips: result.aiTips || [],
              }} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProblemCompilerPage;