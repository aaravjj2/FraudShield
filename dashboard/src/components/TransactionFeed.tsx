import { useEffect, useState, useCallback } from 'react';
import { api } from '../api';
import { Transaction } from '../types';
import { ShapDrawer } from './ShapDrawer';
import './TransactionFeed.css';

interface TransactionFeedProps {
  className?: string;
  onTransactionsUpdate?: (_transactions: Transaction[]) => void;
}

export function TransactionFeed({ className = '', onTransactionsUpdate }: TransactionFeedProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [, setLoadingShap] = useState(false);
  const [searchAmount, setSearchAmount] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'fraud' | 'legit'>('all');

  const fetchTransactions = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getTransactions(50, 0);
      setTransactions(data);
      onTransactionsUpdate?.(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch transactions');
      setLoading(false);
      console.error('Error fetching transactions:', err);
    }
  }, []);

  useEffect(() => {
    fetchTransactions();
    const interval = setInterval(fetchTransactions, 2000);
    return () => clearInterval(interval);
  }, [fetchTransactions]);

  const handleRowClick = async (transaction: Transaction) => {
    setLoadingShap(true);
    // Show drawer immediately with placeholder
    setSelectedTransaction(transaction);
    try {
      const explanation = await api.getExplanation(Number(transaction.id));
      // Update the transaction with SHAP values and base values
      setSelectedTransaction({
        ...transaction,
        top_features: explanation.top_features,
        base_value: explanation.base_value,
        base_probability: explanation.base_probability,
      });
    } catch (err) {
      console.error('Error fetching SHAP explanation:', err);
    } finally {
      setLoadingShap(false);
    }
  };

  const handleCloseDrawer = () => {
    setSelectedTransaction(null);
  };

  if (loading) {
    return (
      <div className={`transaction-feed-section ${className}`} data-testid="transaction-feed">
        <div className="section-header">
          <h2 className="section-title">Transaction Feed</h2>
          <div className="live-indicator">
            <div className="live-dot"></div>
            Live
          </div>
        </div>
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading transactions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`transaction-feed-section ${className}`} data-testid="transaction-feed">
        <div className="section-header">
          <h2 className="section-title">Transaction Feed</h2>
          <div className="live-indicator">
            <div className="live-dot"></div>
            Live
          </div>
        </div>
        <div className="error-state">
          <span>⚠️ {error}</span>
        </div>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className={`transaction-feed-section ${className}`} data-testid="transaction-feed">
        <div className="section-header">
          <h2 className="section-title">Transaction Feed</h2>
          <div className="live-indicator">
            <div className="live-dot"></div>
            Live
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <p>No transactions yet. Submit a test transaction to see it appear here.</p>
        </div>
      </div>
    );
  }

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatProbability = (prob: number): string => {
    return `${(prob * 100).toFixed(1)}%`;
  };

  // Filter transactions based on search amount and status
  const filteredTransactions = transactions.filter((transaction) => {
    // Filter by amount if search is provided
    if (searchAmount !== '') {
      const searchValue = parseFloat(searchAmount);
      if (isNaN(searchValue)) return false;
      if (transaction.amount !== searchValue) return false;
    }

    // Filter by status
    if (filterStatus === 'fraud' && !transaction.is_fraud) return false;
    if (filterStatus === 'legit' && transaction.is_fraud) return false;

    return true;
  });

  return (
    <>
      <div className={`transaction-feed-section ${className}`}>
        <div className="section-header">
          <h2 className="section-title">Transaction Feed</h2>
          <div className="live-indicator">
            <div className="live-dot"></div>
            Live
          </div>
        </div>

        <div className="filter-bar">
          <input
            type="number"
            className="search-input"
            data-testid="search-input"
            placeholder="Search by amount..."
            value={searchAmount}
            onChange={(e) => setSearchAmount(e.target.value)}
            aria-label="Search transactions by amount"
          />
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filterStatus === 'all' ? 'active' : ''}`}
              data-testid="filter-all"
              onClick={() => setFilterStatus('all')}
              aria-label="Show all transactions"
              aria-pressed={filterStatus === 'all'}
            >
              All
            </button>
            <button
              className={`filter-btn ${filterStatus === 'fraud' ? 'active' : ''}`}
              data-testid="filter-fraud"
              onClick={() => setFilterStatus('fraud')}
              aria-label="Show only fraud transactions"
              aria-pressed={filterStatus === 'fraud'}
            >
              Fraud
            </button>
            <button
              className={`filter-btn ${filterStatus === 'legit' ? 'active' : ''}`}
              data-testid="filter-legit"
              onClick={() => setFilterStatus('legit')}
              aria-label="Show only legitimate transactions"
              aria-pressed={filterStatus === 'legit'}
            >
              Legit
            </button>
          </div>
        </div>

        <div className="transaction-feed" data-testid="transaction-feed">
          <table className="transactions-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Amount</th>
                <th>Fraud Probability</th>
                <th>Status</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((transaction) => (
                <tr
                  key={transaction.id}
                  className={transaction.is_fraud ? 'fraud-row' : 'legit-row'}
                  data-testid={transaction.is_fraud ? 'fraud-row' : 'legit-row'}
                  onClick={() => handleRowClick(transaction)}
                  onFocus={(e) => e.currentTarget.click()}
                  tabIndex={0}
                  role="button"
                  aria-label={`View details for transaction ${transaction.id}`}
                >
                  <td>{formatTimestamp(transaction.created_at)}</td>
                  <td>{formatAmount(transaction.amount)}</td>
                  <td>{formatProbability(transaction.fraud_probability)}</td>
                  <td>
                    {transaction.is_fraud ? (
                      <span className="fraud-indicator">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                          <path d="M6 1L1 11h10L6 1zm0 2.5L8.5 9h-5L6 3.5z"/>
                        </svg>
                        FRAUD
                      </span>
                    ) : (
                      <span className="legit-indicator">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                          <path d="M4 6l2 2 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
                        </svg>
                        LEGIT
                      </span>
                    )}
                  </td>
                  <td>{transaction.latency_ms.toFixed(2)}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedTransaction && (
        <ShapDrawer
          transaction={selectedTransaction}
          onClose={handleCloseDrawer}
        />
      )}
    </>
  );
}
