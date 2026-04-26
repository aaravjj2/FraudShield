import { useState, FormEvent } from 'react';
import { api } from '../api';
import { PredictRequest, PredictResponse } from '../types';
import './TestForm.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.port === '5173'
  ? 'http://localhost:8000'
  : '';

interface TestFormProps {
  className?: string;
  onSubmit?: (response: PredictResponse) => void;
}

export function TestForm({ className = '', onSubmit }: TestFormProps) {
  const [amount, setAmount] = useState<string>('100.00');
  const [v1, setV1] = useState<string>('0');
  const [v2, setV2] = useState<string>('0');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<PredictResponse | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const features: number[] = [
        parseFloat(v1) || 0,
        parseFloat(v2) || 0,
        ...Array(26).fill(0)
      ];

      const request: PredictRequest = {
        amount: parseFloat(amount) || 0,
        features
      };

      const result = await api.predict(request);
      setResponse(result);
      onSubmit?.(result);
    } catch (err) {
      setError('Failed to submit prediction. Please try again.');
      console.error('Error submitting prediction:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`test-form-section ${className}`}>
      <div className="section-header">
        <h2 className="section-title">Test Transaction</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="amount-input" className="form-label">
            Transaction Amount (USD)
          </label>
          <input
            id="amount-input"
            type="number"
            step="0.01"
            min="0"
            className="form-input"
            data-testid="amount-input"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="100.00"
            required
            aria-label="Transaction amount in US dollars"
          />
        </div>

        <div className="form-group">
          <label htmlFor="v1-input" className="form-label">
            Feature V1 (PCA Component)
          </label>
          <input
            id="v1-input"
            type="number"
            step="0.001"
            className="form-input"
            data-testid="v1-input"
            value={v1}
            onChange={(e) => setV1(e.target.value)}
            placeholder="0.000"
            aria-label="PCA component V1 value"
          />
        </div>

        <div className="form-group">
          <label htmlFor="v2-input" className="form-label">
            Feature V2 (PCA Component)
          </label>
          <input
            id="v2-input"
            type="number"
            step="0.001"
            className="form-input"
            data-testid="v2-input"
            value={v2}
            onChange={(e) => setV2(e.target.value)}
            placeholder="0.000"
            aria-label="PCA component V2 value"
          />
        </div>

        <div className="advanced-options">
          <button
            type="button"
            className="advanced-toggle"
            onClick={() => setShowAdvanced(!showAdvanced)}
            aria-expanded={showAdvanced}
            aria-controls="advanced-features"
          >
            {showAdvanced ? '▼' : '▶'} Advanced Features (V3-V28)
          </button>

          {showAdvanced && (
            <div id="advanced-features" className="advanced-grid">
              {Array.from({ length: 26 }, (_, i) => i + 3).map((num) => (
                <div key={num} className="form-group">
                  <label
                    htmlFor={`v${num}-input`}
                    className="form-label"
                    style={{ fontSize: '0.75rem' }}
                  >
                    V{num}
                  </label>
                  <input
                    id={`v${num}-input`}
                    type="number"
                    step="0.001"
                    className="form-input"
                    defaultValue="0"
                    aria-label={`PCA component V${num} value`}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          className="submit-btn"
          data-testid="submit-btn"
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? 'Processing...' : 'Submit Prediction'}
        </button>

        <button
          type="button"
          className="submit-btn"
          style={{
            background: 'linear-gradient(135deg, var(--accent-purple) 0%, #7c3aed 100%)',
            marginTop: '0.5rem',
          }}
          disabled={loading}
          onClick={async () => {
            setLoading(true);
            try {
              await fetch(`${API_BASE_URL}/simulate?count=10`, { method: 'POST' });
            } catch (err) {
              console.error('Simulation error:', err);
            } finally {
              setLoading(false);
            }
          }}
        >
          {loading ? 'Simulating...' : 'Simulate 10 Transactions'}
        </button>
      </form>

      {error && (
        <div className="error-state">
          <span>⚠️ {error}</span>
        </div>
      )}

      {response && (
        <div className="prediction-result" data-testid="prediction-result">
          <div className="prediction-result-header">
            <span className="prediction-result-title">Prediction Result</span>
            <span className={`prediction-badge ${response.is_fraud ? 'fraud' : 'legit'}`}>
              {response.is_fraud ? 'FRAUD' : 'LEGITIMATE'}
            </span>
          </div>

          <div className="risk-gauge" data-testid="risk-gauge">
            <div className="risk-gauge-track">
              <div
                className="risk-gauge-fill"
                style={{
                  width: `${response.fraud_probability * 100}%`,
                  background: response.fraud_probability > 0.7
                    ? 'linear-gradient(90deg, #f59e0b, #ef4444)'
                    : response.fraud_probability > 0.3
                      ? 'linear-gradient(90deg, #10b981, #f59e0b)'
                      : 'linear-gradient(90deg, #10b981, #34d399)',
                }}
              />
            </div>
            <div className="risk-gauge-labels">
              <span>Low Risk</span>
              <span className="risk-gauge-value">
                {(response.fraud_probability * 100).toFixed(1)}%
              </span>
              <span>High Risk</span>
            </div>
          </div>

          <div className="prediction-details">
            <div className="prediction-detail-row">
              <span className="detail-label">Latency</span>
              <span className="detail-value">{response.latency_ms.toFixed(2)}ms</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
