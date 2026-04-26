import { Transaction } from '../types';
import './ShapDrawer.css';

interface ShapDrawerProps {
  transaction: Transaction;
  onClose: () => void;
}

export function ShapDrawer({ transaction, onClose }: ShapDrawerProps) {
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const topFeatures = transaction.top_features.slice(0, 5);

  const maxShapValue = Math.max(
    ...topFeatures.map((f) => Math.abs(f.shap_value)),
    1
  );

  const getBarWidth = (shapValue: number): number => {
    return (Math.abs(shapValue) / maxShapValue) * 100;
  };

  return (
    <div
      className="shap-drawer-overlay open"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="drawer-title"
      data-testid="shap-drawer"
    >
      <div className="shap-drawer">
        <div className="drawer-header">
          <h2 id="drawer-title" className="drawer-title">
            Transaction Analysis
          </h2>
          <button
            className="drawer-close"
            onClick={onClose}
            aria-label="Close drawer"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="drawer-content">
          <div className="shap-waterfall">
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Top 5 Contributing Features
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Each bar shows how much a feature pushed the prediction toward fraud
                (red) or legitimate (green). Larger bars = stronger influence.
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.375rem', opacity: 0.8 }}>
                SHAP values comply with EU AI Act Art.13 explainability requirements.
              </p>
            </div>

            {topFeatures.map((feature: { feature: string; shap_value: number }, index: number) => {
              const barWidth = getBarWidth(feature.shap_value);
              const isPositive = feature.shap_value > 0;

              return (
                <div
                  key={feature.feature || index}
                  className="shap-bar"
                  data-testid="shap-bar"
                >
                  <div className="shap-bar-feature">
                    {feature.feature || `V${index + 1}`}
                  </div>
                  <div className={`shap-bar-value ${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? '+' : ''}{feature.shap_value.toFixed(4)}
                  </div>
                  <div className="shap-bar-visual">
                    <div
                      className={`shap-bar-fill ${isPositive ? 'positive' : 'negative'}`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="transaction-details">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
              Transaction Details
            </h3>

            <div className="detail-row">
              <div className="detail-label">Transaction ID</div>
              <div className="detail-value">{transaction.id}</div>
            </div>

            <div className="detail-row">
              <div className="detail-label">Amount</div>
              <div className="detail-value">{formatAmount(transaction.amount)}</div>
            </div>

            <div className="detail-row">
              <div className="detail-label">Fraud Probability</div>
              <div className="detail-value" style={{ color: transaction.is_fraud ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {(transaction.fraud_probability * 100).toFixed(2)}%
              </div>
            </div>

            <div className="detail-row">
              <div className="detail-label">Status</div>
              <div className="detail-value" style={{ color: transaction.is_fraud ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {transaction.is_fraud ? 'FRAUD' : 'LEGITIMATE'}
              </div>
            </div>

            <div className="detail-row">
              <div className="detail-label">Prediction Latency</div>
              <div className="detail-value">{transaction.latency_ms.toFixed(2)}ms</div>
            </div>

            <div className="detail-row">
              <div className="detail-label">Timestamp</div>
              <div className="detail-value">{formatTimestamp(transaction.created_at)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
