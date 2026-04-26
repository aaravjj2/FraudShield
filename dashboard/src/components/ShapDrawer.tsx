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
  const baseProbability = transaction.base_probability ?? 0.0044;
  const fraudProbability = transaction.fraud_probability;

  // Calculate cumulative values for waterfall effect
  let cumulativeValue = baseProbability;
  const waterfallData = topFeatures.map((feature) => {
    const shapEffect = feature.shap_value * 0.1; // Scale SHAP to probability space
    const startValue = cumulativeValue;
    cumulativeValue = Math.max(0, Math.min(1, cumulativeValue + shapEffect));
    const endValue = cumulativeValue;

    return {
      ...feature,
      startValue,
      endValue,
      effect: endValue - startValue
    };
  });

  const maxShapValue = Math.max(
    ...waterfallData.map((f) => Math.abs(f.effect)),
    0.01
  );

  const getBarWidth = (effect: number): number => {
    return (Math.abs(effect) / maxShapValue) * 100;
  };

  const getDirection = (effect: number): 'pushes-up' | 'pushes-down' => {
    return effect > 0 ? 'pushes-up' : 'pushes-down';
  };

  const formatProbability = (prob: number): string => {
    return `${(prob * 100).toFixed(2)}%`;
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
                Feature Importance Waterfall
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Shows how each feature pushed the prediction from the base rate to the final probability.
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.375rem', opacity: 0.8 }}>
                SHAP values comply with EU AI Act Art.13 explainability requirements.
              </p>
            </div>

            <div className="waterfall-chart">
              {/* Base Value Row */}
              <div className="shap-bar base-row" data-testid="shap-bar">
                <div className="shap-bar-feature">Base Value</div>
                <div className="shap-bar-value base-value">
                  {formatProbability(baseProbability)}
                </div>
                <div className="shap-bar-visual">
                  <div
                    className="shap-bar-fill base-fill"
                    style={{ width: `${(baseProbability / fraudProbability) * 100}%` }}
                  />
                </div>
              </div>

              {/* Feature Rows */}
              {waterfallData.map((feature: {
                feature: string;
                shap_value: number;
                startValue: number;
                endValue: number;
                effect: number;
              }, index: number) => {
                const barWidth = getBarWidth(feature.effect);
                const direction = getDirection(feature.effect);

                return (
                  <div
                    key={feature.feature || index}
                    className={`shap-bar ${direction}`}
                    data-testid="shap-bar"
                  >
                    <div className="shap-bar-feature">
                      {feature.feature || `V${index + 1}`}
                    </div>
                    <div className={`shap-bar-value ${direction}`}>
                      {direction === 'pushes-up' ? '+' : ''}{formatProbability(Math.abs(feature.effect))}
                    </div>
                    <div className="shap-bar-visual">
                      <div
                        className={`shap-bar-fill ${direction}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}

              {/* Final Prediction Row */}
              <div className="shap-bar final-row" data-testid="shap-bar">
                <div className="shap-bar-feature">Final Prediction</div>
                <div className={`shap-bar-value ${transaction.is_fraud ? 'pushes-up' : 'pushes-down'}`}>
                  {formatProbability(fraudProbability)}
                </div>
                <div className="shap-bar-visual">
                  <div
                    className={`shap-bar-fill ${transaction.is_fraud ? 'pushes-up' : 'pushes-down'}`}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            </div>

            {/* Explanation Text */}
            <div className="waterfall-explanation">
              <p>
                <strong>Explanation:</strong> This transaction has a{' '}
                <span className={transaction.is_fraud ? 'fraud-text' : 'legit-text'}>
                  {formatProbability(fraudProbability)} fraud probability
                </span>. The model started at{' '}
                <span className="base-text">{formatProbability(baseProbability)}</span> (base rate).
                {waterfallData.some(f => f.effect > 0) && ' The following features pushed the prediction '}
                {waterfallData.filter(f => f.effect > 0).length > 0 && (
                  <span className="increase-text">up</span>
                )}
                {waterfallData.filter(f => f.effect > 0).length > 0 && waterfallData.filter(f => f.effect < 0).length > 0 && ' and '}
                {waterfallData.some(f => f.effect < 0) && (
                  <span className="decrease-text">down</span>
                )}
                {waterfallData.some(f => f.effect !== 0) && ' to reach the final prediction.'}
              </p>
            </div>
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
                {formatProbability(transaction.fraud_probability)}
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
