import React from 'react';
import '../styles/Console.css';

const Console = ({ result }) => {
  if (!result) {
    return (
      <div className="console-content empty">
        Click "Run Code" to see output...
      </div>
    );
  }

  const getVerdictClass = (verdict) => {
    switch (verdict) {
      case 'ACCEPTED': return 'success';
      case 'TIME_LIMIT_EXCEEDED': return 'warning';
      default: return 'error';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'ACCEPTED': return '✓';
      case 'TIME_LIMIT_EXCEEDED': return '⏱';
      case 'MEMORY_LIMIT_EXCEEDED': return '💾';
      default: return '✗';
    }
  };

  const formatVerdict = (verdict) => verdict?.replace(/_/g, ' ') ?? '';

  return (
    <div className="console-content">

      {/* ── VERDICT BADGE ── */}
      <div className={`verdict-badge ${getVerdictClass(result.verdict)}`}>
        {getVerdictIcon(result.verdict)} {formatVerdict(result.verdict)}
      </div>

      {/* ── ACCEPTED ── */}
      {result.verdict === 'ACCEPTED' && (
        <>
          <div className="test-summary success">All test cases passed!</div>
          {(result.executionTimeMs || result.memoryUsedKb) && (
            <div className="stats-row">
              {result.executionTimeMs && (
                <span>⏱ Runtime: {result.executionTimeMs.toFixed(0)}ms</span>
              )}
              {result.memoryUsedKb && (
                <span>💾 Memory: {(result.memoryUsedKb / 1024).toFixed(2)}MB</span>
              )}
            </div>
          )}
        </>
      )}

      {/* ── WRONG ANSWER ── */}
      {result.verdict === 'WRONG_ANSWER' && (
        <>
          <div className="test-summary error">
            {result.passedTests}/{result.totalTests} test cases passed
          </div>
          {result.firstFailedInput != null && (
            <div className="failed-test">
              <div className="failed-header">First Failed Test:</div>
              <div className="test-detail">
                <strong>Input:</strong>
                <pre className="test-code">{result.firstFailedInput}</pre>
              </div>
              <div className="test-detail">
                <strong>Expected:</strong>
                <pre className="test-code expected">{result.firstFailedExpected}</pre>
              </div>
              <div className="test-detail">
                <strong>Your Output:</strong>
                <pre className="test-code actual">{result.firstFailedActual || '(empty)'}</pre>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── COMPILATION ERROR ── */}
      {result.verdict === 'COMPILATION_ERROR' && (
        <div className="error-block">
          <div className="error-block-title">Compilation Error</div>
          <pre className="error-pre">
            {result.compilationError
              ?.replace(/^Runtime Error \(NZEC\)\n?/i, '')
              .trim() || 'No details available.'}
          </pre>
        </div>
      )}

      {/* ── RUNTIME ERROR ── */}
      {result.verdict === 'RUNTIME_ERROR' && (
        <>
          <div className="test-summary error">
            {result.passedTests}/{result.totalTests} test cases passed
          </div>
          {result.firstFailedInput && (
            <div className="failed-test">
              <div className="failed-header">Failed on:</div>
              <div className="test-detail">
                <strong>Input:</strong>
                <pre className="test-code">{result.firstFailedInput}</pre>
              </div>
            </div>
          )}
          <div className="error-block">
            <div className="error-block-title">Runtime Error Details</div>
            <pre className="error-pre">{result.runtimeError || 'No details available.'}</pre>
          </div>
        </>
      )}

      {/* ── TIME LIMIT EXCEEDED ── */}
      {result.verdict === 'TIME_LIMIT_EXCEEDED' && (
        <>
          <div className="test-summary warning">
            {result.passedTests}/{result.totalTests} test cases passed before timeout
          </div>
          {result.firstFailedInput && (
            <div className="failed-test">
              <div className="failed-header">Timed out on:</div>
              <div className="test-detail">
                <strong>Input:</strong>
                <pre className="test-code">{result.firstFailedInput}</pre>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── MEMORY LIMIT EXCEEDED ── */}
      {result.verdict === 'MEMORY_LIMIT_EXCEEDED' && (
        <>
          <div className="test-summary error">
            {result.passedTests}/{result.totalTests} test cases passed before memory limit
          </div>
          <div className="error-block">
            <div className="error-block-title">Memory Limit Exceeded</div>
            <p className="error-hint">Your solution used too much memory. Check for memory leaks or large data structures.</p>
          </div>
        </>
      )}

    </div>
  );
};

export default Console;