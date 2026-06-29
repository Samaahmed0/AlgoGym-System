import React, { useState } from 'react';
import '../styles/ProblemPanel.css';
import MathText from './MathText';
import TextWithImages from './TextWithImages';
import { useNavigate } from 'react-router-dom';

const ProblemPanel = ({ problem, submissions }) => {
  const [activeTab, setActiveTab] = useState('description');
  const [editorialOpen, setEditorialOpen] = useState(false);
  const examples = problem.examples || [];
  const navigate = useNavigate();

  return (
    <div className="problem-panel">

      {/* Tabs */}
      <div className="problem-tabs">
        <button className="back-btn" onClick={() => navigate(-1)}>❮</button>
        <button
          className={`tab ${activeTab === 'description' ? 'active' : ''}`}
          onClick={() => setActiveTab('description')}
        >
          Description
        </button>
        <button
          className={`tab ${activeTab === 'submissions' ? 'active' : ''}`}
          onClick={() => setActiveTab('submissions')}
        >
          Submissions ({submissions?.length || 0})
        </button>
      </div>

      {/* Description Tab */}
      {activeTab === 'description' && (
        <>
          <div className="problem-header">
            <h1>{problem.title}</h1>
            <span className={`difficulty ${problem.difficulty?.toLowerCase()}`}>
              {problem.difficulty}
            </span>
          </div>

          <div className="problem-content">
            <section>
              <h3>Description</h3>
              <p className="description">
                <TextWithImages text={problem.description} />
              </p>
            </section>

            {problem.inputFormat && (
              <section className="format">
                <h3>Input Format</h3>
                <p className="description"><MathText text={problem.inputFormat} /></p>
              </section>
            )}

            {problem.outputFormat && (
              <section className="format">
                <h3>Output Format</h3>
                <p className="description"><MathText text={problem.outputFormat} /></p>
              </section>
            )}

            {examples.length > 0 && (
              <section>
                <h3>Examples</h3>
                <div className="examples-grid">
                  {examples.map((example, index) => (
                    <div key={index} className="example-card">
                      <div className="example-label">Example {index + 1}</div>
                      <div className="example-row">
                        <div className="example-col">
                          <div className="example-col-label">Input</div>
                          <pre className="example-code">{example.input}</pre>
                        </div>
                        <div className="example-col">
                          <div className="example-col-label">Output</div>
                          <pre className="example-code">{example.output}</pre>
                        </div>
                      </div>
                      {example.explanation && (
                        <div className="example-explanation">
                          <strong>Explanation:</strong> <MathText text={example.explanation} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {problem.note && (
              <section>
                <h3>Note</h3>
                <p className="description"><TextWithImages text={problem.note} /></p>
              </section>
            )}

            {/* Editorial / Hint */}
            {problem.editorial && problem.editorial.trim() !== "" && (
              <section>
                <button
                  className={`editorial-toggle ${editorialOpen ? 'open' : ''}`}
                  onClick={() => setEditorialOpen(!editorialOpen)}
                >
                  <span>💡 Hint</span>
                  <span className="hint-arrow">{editorialOpen ? '▲' : '▼'}</span>
                </button>
                {editorialOpen && (
                  <div className="editorial-content">
                    <MathText text={problem.editorial} />
                  </div>
                )}
              </section>
            )}

            {/* Limits & Tags */}
            <section className="limits">
              <div className="limits-row">
                <div className="limit-item">
                  <strong>Time Limit:</strong> {problem.timeLimit}s
                </div>
                <div className="limit-item">
                  <strong>Memory Limit:</strong> {problem.memoryLimit}MB
                </div>
              </div>
              {problem.tags?.length > 0 && (
                <div className="tags-row">
                  {problem.tags.map((tag, i) => (
                    <span key={i} className="tag-chip">{tag}</span>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {/* Submissions Tab */}
      {activeTab === 'submissions' && (
        <div className="submissions-container">
          <h2>Your Submissions</h2>
          {!submissions || submissions.length === 0 ? (
            <div className="no-submissions">
              <p>No submissions yet. Click Submit to test your code!</p>
            </div>
          ) : (
            <div className="submissions-list">
              {submissions
                .sort((a, b) => new Date(b.submittedAt) - new Date(a.submittedAt)) // newest first
                .map((sub, index) => (
                  <div key={index} className="submission-card">
                    <div className="submission-header">
                      <span className={`verdict ${sub.verdict.toLowerCase().replace(/_/g, '-')}`}>
                        {sub.verdict === 'ACCEPTED' ? '✓' : '✗'} {sub.verdict.replace(/_/g, ' ')}
                      </span>
                      <span className="submission-time">
                        {new Date(sub.submittedAt).toLocaleString()}
                      </span>
                    </div>
                    <div className="submission-details">
                      <div className="detail-item">
                        <strong>Tests:</strong> {sub.passedTests}/{sub.totalTests}
                      </div>
                      <div className="detail-item">
                        <strong>Language:</strong> {sub.languageName}
                      </div>
                      <div className="detail-item">
                        <strong>Runtime:</strong> {sub.executionTimeMs ? `${sub.executionTimeMs.toFixed(0)}ms` : 'N/A'}
                      </div>
                      <div className="detail-item">
                        <strong>Memory:</strong> {sub.memoryUsedKb ? `${(sub.memoryUsedKb / 1024).toFixed(1)}MB` : 'N/A'}
                      </div>
                    </div>
                  </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
};

export default ProblemPanel;