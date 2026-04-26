import { useState, FormEvent } from 'react';
import { api } from '../api';
import { PredictRequest, PredictResponse } from '../types';
import './TestForm.css';

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
      </form>

      {error && (
        <div className="error-state">
          <span>⚠️ {error}</span>
        </div>
      )}

      {response && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-primary)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
          <div style={{ marginBottom: '0.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Prediction Result
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            <div style={{ marginBottom: '0.25rem' }}>
              Fraud Probability: <span style={{ color: response.is_fraud ? 'var(--accent-red)' : 'var(--accent-green)', fontWeight: 600 }}>
                {(response.fraud_probability * 100).toFixed(1)}%
              </span>
            </div>
            <div style={{ marginBottom: '0.25rem' }}>
              Status: <span style={{ fontWeight: 600 }}>{response.is_fraud ? 'FRAUD' : 'LEGITIMATE'}</span>
            </div>
            <div>
              Latency: <span style={{ fontWeight: 600 }}>{response.latency_ms.toFixed(2)}ms</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
