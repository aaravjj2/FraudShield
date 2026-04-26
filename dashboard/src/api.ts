import {
  PredictRequest,
  PredictResponse,
  BatchRequest,
  BatchResponse,
  Transaction,
  StatsResponse,
  HealthResponse
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.port === '5173'
  ? 'http://localhost:8000'  // Dev mode: direct API access
  : '';  // Production/Docker: same origin via nginx proxy

export const api = {
  async predict(request: PredictRequest): Promise<PredictResponse> {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async batchPredict(request: BatchRequest): Promise<BatchResponse> {
    const response = await fetch(`${API_BASE_URL}/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getTransactions(limit: number = 50, offset: number = 0): Promise<Transaction[]> {
    const response = await fetch(
      `${API_BASE_URL}/transactions?limit=${limit}&offset=${offset}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getStats(): Promise<StatsResponse> {
    const response = await fetch(`${API_BASE_URL}/stats`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
};
