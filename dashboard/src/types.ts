export interface Transaction {
  id: string;
  amount: number;
  fraud_probability: number;
  is_fraud: boolean;
  top_features: Array<{
    feature: string;
    shap_value: number;
  }>;
  latency_ms: number;
  created_at: string;
  base_value?: number;
  base_probability?: number;
}

export interface PredictRequest {
  amount: number;
  features: number[];
}

export interface PredictResponse {
  fraud_probability: number;
  is_fraud: boolean;
  top_features: Array<{
    feature: string;
    shap_value: number;
  }>;
  latency_ms: number;
  transaction_id: string;
}

export interface BatchRequest {
  transactions: PredictRequest[];
}

export interface BatchResponse {
  results: PredictResponse[];
  total_latency_ms: number;
}

export interface StatsResponse {
  total_transactions: number;
  total_fraud: number;
  fraud_rate: number;
  avg_latency_ms: number;
  model_f1: number;
  model_auc_roc: number;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
}

export interface ExplainResponse {
  transaction_id: number;
  fraud_probability: number;
  is_fraud: boolean;
  base_value: number;
  base_probability: number;
  top_features: Array<{
    feature: string;
    shap_value: number;
  }>;
  latency_ms: number;
}
