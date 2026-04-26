import { StatsBar } from './components/StatsBar';
import { TransactionFeed } from './components/TransactionFeed';
import { TestForm } from './components/TestForm';
import { PredictResponse } from './types';
import './App.css';

function App() {
  const handlePredictionSubmit = (_response: PredictResponse) => {
    // Transaction feed auto-refreshes via polling
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </span>
            <div className="logo-text">
              <h1 className="logo-title">FraudShield</h1>
              <span className="logo-subtitle">AI-Powered Fraud Detection</span>
            </div>
          </div>
        </div>
        <div className="header-right">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="api-docs-link"
          >
            API Docs
          </a>
        </div>
      </header>

      <StatsBar />

      <main className="main-content">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <TransactionFeed />
        </div>

        <TestForm onSubmit={handlePredictionSubmit} />
      </main>

      <footer className="app-footer">
        <p>
          FraudShield — Real-Time Fraud Detection with SHAP Explainability
        </p>
        <p className="footer-note">
          Explainability complies with EU AI Act Art.13 &amp; SR 11-7 Model Validation requirements
        </p>
      </footer>
    </div>
  );
}

export default App;
