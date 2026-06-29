import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import '../styles/CodeEditor.css';
import { getTemplate } from '../utils/languageTemplates';

const getMonacoLanguage = (judgeName) => {
  if (!judgeName) return 'plaintext';
  const name = judgeName.toLowerCase();
  if (name.includes('python') || name.includes('pypy')) return 'python';
  if (name.includes('javascript') || name.includes('node')) return 'javascript';
  if (name.includes('typescript')) return 'typescript';
  if (name.includes('java')) return 'java';
  if (name.includes('c++') || name.includes('cpp')) return 'cpp';
  if (name.includes('c#') || name.includes('csharp')) return 'csharp';
  if (name.includes('go (') || name.includes('golang')) return 'go';
  if (name.includes('rust')) return 'rust';
  if (name.includes('ruby')) return 'ruby';
  if (name.includes('kotlin')) return 'kotlin';
  if (name.includes('swift')) return 'swift';
  if (name.includes('scala')) return 'scala';
  if (name.includes('php')) return 'php';
  if (name.includes('c ') || name.includes('gcc') || name.includes('clang')) return 'c';
  if (name.includes('r ') || name.includes('r,')) return 'r';
  return 'plaintext';
};

const CodeEditor = ({ onRunCode, onSubmitCode, isRunning, isSubmitting }) => {
  const [code, setCode] = useState('// Write your solution here\n');
  const [languages, setLanguages] = useState([]);
  const [selectedLanguage, setSelectedLanguage] = useState(null);

  // fetch languages from backend
  useEffect(() => {
    fetch('http://localhost:8080/api/languages')
      .then(res => res.json())
      .then(data => {
        setLanguages(data);
        if (data.length > 0) {
          setSelectedLanguage(data[0]);
          setCode(getTemplate(data[0].id));
        }
      })
      .catch(err => console.error('Failed to load languages:', err));
  }, []);

  //swap the template when language is changed
  const handleLanguageChange = (e) => {
    const lang = languages.find(l => l.id === Number(e.target.value));
    if (!lang) return;
    setSelectedLanguage(lang);
    setCode(getTemplate(lang.id));
  };

  const handleRunCode = () => {
    if (!selectedLanguage) return;
    onRunCode(code, selectedLanguage.id, selectedLanguage.name);
  };

  const handleSubmitCode = () => {
    if (!selectedLanguage) return;
    onSubmitCode(code, selectedLanguage.id, selectedLanguage.name);
  };

  return (
    <div className="code-editor-container">
      <div className="editor-header">
        <select
          value={selectedLanguage?.id || ''}
          onChange={handleLanguageChange}
          className="language-select"
        >
          {languages.map(lang => (
            <option key={lang.id} value={lang.id}>
              {lang.name}
            </option>
          ))}
        </select>

        <div className="button-group">
          <button
            onClick={handleRunCode}
            disabled={isRunning || isSubmitting}
            className="run-button"
          >
            {isRunning ? '⏳ Running...' : '▶ Run Code'}
          </button>
          <button
            onClick={handleSubmitCode}
            disabled={isRunning || isSubmitting}
            className="submit-button"
          >
            {isSubmitting ? '⏳ Submitting...' : '✔ Submit'}
          </button>
        </div>
      </div>

      <Editor
        height="100%"
        language={getMonacoLanguage(selectedLanguage?.name)}
        theme="vs-light"
        value={code}
        onChange={(value) => setCode(value ?? '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
        }}
      />
    </div>
  );
};

export default CodeEditor;