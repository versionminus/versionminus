import React, { useEffect } from 'react';
import './LandingPage.css';

type LandingPageProps = {
  onRegister: () => void;
};

export function LandingPage({ onRegister }: LandingPageProps) {
  useEffect(() => {
    const host = window.location.hostname.toLowerCase();
    if (host === 'www.versionminus.com') {
      const target = `https://versionminus.com${window.location.pathname}${window.location.search}${window.location.hash}`;
      window.location.replace(target);
    }
  }, []);

  return (
    <div className="landing-screen">
      <div className="landing-shell">
        <div className="landing-glow" aria-hidden="true" />
        <div className="landing-container">
          <div className="landing-hero">
            <div className="landing-logo">
              <img src="/logo.jpeg" alt="versionminus logo" />
            </div>
            <div>
              <h1 className="landing-title">versionminus</h1>
              <p className="landing-tagline">Human potential, thoughtfully augmented.</p>
            </div>
          </div>

          <div className="landing-panel landing-message">
            <p>
              Welcome to <code className="landing-inline-code">versionminus</code>. We're committed to assist you
              with becoming the best version of yourself by learning from your past behaviour and providing AI
              assisted decision making.
            </p>
            <div className="landing-beta">
              <span className="landing-pill">beta</span>
              <span className="landing-muted">
                Register{' '}
                <button type="button" className="landing-link-button" onClick={onRegister}>
                  here
                </button>{' '}
                to be considered for access to the beta release. For any questions, email{' '}
                <a className="landing-email" href="mailto:diogo@versionminus.com">
                  diogo@versionminus.com
                </a>
                .
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
