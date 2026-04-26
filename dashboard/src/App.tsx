import { StatsBar } from './components/StatsBar';
import { TransactionFeed } from './components/TransactionFeed';
import { TestForm } from './components/TestForm';
import { PredictResponse } from './types';
import './App.css';

function App() {
  const handlePredictionSubmit = (response: PredictResponse) => {
    console.log('Prediction submitted:', response);
  };

  return (
    <div className="app-container">
      <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: 'var(--accent-red)' }}>⚡</span>
          FraudShield
          <span style={{ fontSize: '0.875rem', fontWeight: 400, color: 'var(--text-muted)', marginLeft: 'auto' }}>
            Real-Time AI Fraud Detection
          </span>
        </h1>
      </header>

      <StatsBar />

      <main className="main-content">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <TransactionFeed />
        </div>

        <TestForm onSubmit={handlePredictionSubmit} />
      </main>

      <footer style={{ padding: '1.5rem 2rem', borderTop: '1px solid var(--border-color)', background: 'var(--bg-secondary)', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        <p>FraudShield Dashboard — Real-Time Fraud Detection with SHAP Explainability</p>
        <p style={{ marginTop: '0.5rem' }}>
          API: <code style={{ background: 'var(--bg-primary)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem' }}>http://localhost:8000/docs</code>
        </p>
      </footer>
    </div>
  );
}

export default App;
