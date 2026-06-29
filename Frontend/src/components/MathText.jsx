import katex from 'katex';
import 'katex/dist/katex.min.css';

const MathText = ({ text }) => {
  if (!text) return null;

  const parts = text.split('$$$');

  const cleanLatex = (str) => {
    if (!str) return str;

    return str
      .replace(/\\\\/g, '\\') 
      .replace(/%/g, '\\%')
      .replace(/\r/g, '')
      .trim();
  };

  const renderTextWithLatex = (str, key) => {
    const latexRegex = /(\\sum|\\frac|\\sqrt|\\le|\\ge|\\limits|\\lceil|\\rceil)/;

    if (!latexRegex.test(str)) {
      return (
        <span key={key} style={{ whiteSpace: 'pre-wrap' }}>
          {str}
        </span>
      );
    }

    try {
      const html = katex.renderToString(cleanLatex(str), {
        throwOnError: false,
        displayMode: true
      });

      return (
        <span
          key={key}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    } catch {
      return (
        <span key={key} style={{ whiteSpace: 'pre-wrap' }}>
          {str}
        </span>
      );
    }
  };

  return (
    <span>
      {parts.map((part, index) => {
       
        if (index % 2 === 1) {
          try {
            const html = katex.renderToString(cleanLatex(part), {
              throwOnError: false,
              displayMode: false
            });

            return (
              <span
                key={index}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            );
          } catch {
            return <span key={index}>{part}</span>;
          }
        }
        return renderTextWithLatex(part, index);
      })}
    </span>
  );
};

export default MathText;