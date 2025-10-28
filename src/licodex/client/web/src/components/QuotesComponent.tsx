import React, { useCallback, useEffect, useRef, useState } from 'react';
import './ChatPanelQuotes.css';

interface Quote { quote: string; author: string; }

const MIN_CHAR_DELAY_MS = 35;
const MAX_CHAR_DELAY_MS = 180;
const PUNCTUATION_EXTRA_DELAY_MS = 220;
const QUOTE_END_DELAY_MS = 2500;

export const QuotesComponent: React.FC = () => {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [index, setIndex] = useState(0);
  const [displayedChars, setDisplayedChars] = useState(0);
  const [authorFadeKey, setAuthorFadeKey] = useState(0);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    fetch('/quotes.json')
      .then(r => r.json())
      .then((data: Quote[]) => {
        if (Array.isArray(data) && data.length) {
          const arr = data.slice();
          for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
          }
          setQuotes(arr);
        }
      })
      .catch(() => { /* silent */ });
  }, []);

  const scheduleNextChar = useCallback((full: string) => {
    if (displayedChars >= full.length) {
      timeoutRef.current = window.setTimeout(() => {
        setIndex(i => (quotes.length ? (i + 1) % quotes.length : 0));
        setDisplayedChars(0);
        setAuthorFadeKey(k => k + 1);
      }, QUOTE_END_DELAY_MS);
      return;
    }
    const nextChar = full[displayedChars];
    let delay = MIN_CHAR_DELAY_MS + Math.random() * (MAX_CHAR_DELAY_MS - MIN_CHAR_DELAY_MS);
    if (/[.,;:!?]/.test(nextChar)) {
      delay += PUNCTUATION_EXTRA_DELAY_MS * Math.random();
    }
    timeoutRef.current = window.setTimeout(() => setDisplayedChars(c => c + 1), delay);
  }, [displayedChars, quotes.length]);

  useEffect(() => {
    if (!quotes.length) return;
    scheduleNextChar(quotes[index].quote);
    return () => { if (timeoutRef.current) window.clearTimeout(timeoutRef.current); };
  }, [quotes, index, displayedChars, scheduleNextChar]);

  useEffect(() => { if (quotes.length) { setDisplayedChars(0); setAuthorFadeKey(k => k + 1); } }, [quotes.length]);

  if (!quotes.length) return null;
  const current = quotes[index];
  const visibleQuote = current.quote.slice(0, displayedChars);

  return (
    <div className="center-fill">
      <div className="quotes-centered-container">
        <div key={authorFadeKey} className="quotes-author fade-cycle">{current.author}</div>
        <div className="quotes-quote">{visibleQuote}<span className="cursor">{displayedChars < current.quote.length ? '▌' : ' '}</span></div>
      </div>
    </div>
  );
};

export default QuotesComponent;
