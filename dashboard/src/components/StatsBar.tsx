import { useEffect, useState } from 'react';
import { api } from '../api';
import { StatsResponse } from '../types';
import './StatsBar.css';

interface StatsBarProps {
  className?: string;
}

export function StatsBar({ className = '' }: StatsBarProps) {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setError(null);
        const data = await api.getStats();
        setStats(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch stats');
        setLoading(false);
        console.error('Error fetching stats:', err);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className={`stats-bar ${className}`} data-testid="stats-bar">
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="stat-card">
              <div className="stat-label">Loading...</div>
              <div className="stat-value">—</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className={`stats-bar ${className}`} data-testid="stats-bar">
        <div className="error-state">
          <span>⚠️ {error || 'Failed to load stats'}</span>
        </div>
      </div>
    );
  }

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatDecimal = (value: number): string => {
    return value.toFixed(4);
  };

  const formatLatency = (value: number): string => {
    return `${value.toFixed(2)}ms`;
  };

  return (
    <div className={`stats-bar ${className}`} data-testid="stats-bar">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div className="stat-label">Total Transactions</div>
          <div className="stat-value blue">{stats.total_transactions.toLocaleString()}</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div className="stat-label">Fraud Detected</div>
          <div className="stat-value red">{stats.total_fraud.toLocaleString()}</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <div className="stat-label">Fraud Rate</div>
          <div className="stat-value red">{formatPercentage(stats.fraud_rate)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <div className="stat-label">Model F1 Score</div>
          <div className="stat-value green">{formatDecimal(stats.model_f1)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div className="stat-label">Model AUC-ROC</div>
          <div className="stat-value purple">{formatDecimal(stats.model_auc_roc)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon yellow">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div className="stat-label">Avg Latency</div>
          <div className="stat-value">{formatLatency(stats.avg_latency_ms)}</div>
        </div>
      </div>
    </div>
  );
}
