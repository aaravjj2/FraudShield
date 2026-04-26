import { useEffect, useState, useCallback, useRef } from 'react';
import { Transaction } from '../types';

interface FraudAlert {
  id: string;
  amount: number;
  fraud_probability: number;
  timestamp: number;
}

interface FraudAlertProps {
  transactions: Transaction[];
}

export function FraudAlert({ transactions }: FraudAlertProps) {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const seenIds = useRef<Set<string>>(new Set());

  const detectNewFraud = useCallback((txs: Transaction[]) => {
    const newFraudAlerts: FraudAlert[] = [];
    for (const tx of txs) {
      if (tx.is_fraud && !seenIds.current.has(tx.id)) {
        seenIds.current.add(tx.id);
        newFraudAlerts.push({
          id: tx.id,
          amount: tx.amount,
          fraud_probability: tx.fraud_probability,
          timestamp: Date.now(),
        });
      } else if (!tx.is_fraud) {
        seenIds.current.add(tx.id);
      }
    }
    if (newFraudAlerts.length > 0) {
      setAlerts(prev => [...newFraudAlerts, ...prev].slice(0, 5));
    }
  }, []);

  useEffect(() => {
    detectNewFraud(transactions);
  }, [transactions, detectNewFraud]);

  // Auto-dismiss alerts after 6s
  useEffect(() => {
    if (alerts.length === 0) return;
    const timer = setTimeout(() => {
      setAlerts(prev => prev.slice(0, -1));
    }, 6000);
    return () => clearTimeout(timer);
  }, [alerts]);

  const dismissAlert = (id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  if (alerts.length === 0) return null;

  return (
    <div className="fraud-alert-container" data-testid="fraud-alert-container">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="fraud-alert-toast"
          data-testid="fraud-alert-toast"
          role="alert"
        >
          <div className="fraud-alert-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div className="fraud-alert-content">
            <div className="fraud-alert-title">Fraud Detected</div>
            <div className="fraud-alert-detail">
              ${alert.amount.toFixed(2)} — {(alert.fraud_probability * 100).toFixed(1)}% probability
            </div>
          </div>
          <button
            className="fraud-alert-dismiss"
            onClick={() => dismissAlert(alert.id)}
            aria-label="Dismiss alert"
            data-testid="fraud-alert-dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="1" y1="1" x2="13" y2="13"/>
              <line x1="13" y1="1" x2="1" y2="13"/>
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
