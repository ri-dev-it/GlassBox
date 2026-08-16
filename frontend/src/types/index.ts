export type Role = 'applicant' | 'loan_officer' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export type ApplicantFeatures = Record<string, string | number>;

export interface PredictionResult {
  id: number;
  application_id: number;
  decision: 'APPROVED' | 'REJECTED';
  probability: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  model_name: string;
  created_at: string;
}

export interface Contribution {
  feature: string;
  label: string;
  value: string | number;
  contribution: number;
  direction: 'positive' | 'negative';
}

export interface ExplanationResult {
  id?: number;
  prediction_id?: number;
  method?: 'shap' | 'lime';
  contributions: Contribution[];
  plain_english: string;
}

export interface ComparisonResult {
  agreement: Array<{
    feature: string;
    label: string;
    shap_contribution: number;
    lime_contribution: number;
    shap_direction: string;
    lime_direction: string;
  }>;
  direction_disagreement: Array<{
    feature: string;
    label: string;
    shap_contribution: number;
    lime_contribution: number;
    shap_direction: string;
    lime_direction: string;
  }>;
  shap_only_top_features: string[];
  lime_only_top_features: string[];
  note: string;
}

export interface CounterfactualAlternative {
  [feature: string]: { label: string; current: string | number; suggested: string | number };
}

export interface CounterfactualResult {
  found: boolean;
  message: string;
  current_profile: ApplicantFeatures;
  alternatives: CounterfactualAlternative[];
}

export interface ApplicationDetail {
  application: {
    id: number;
    application_id: string;
    status: string;
    applicant_id: number;
    features: ApplicantFeatures;
    created_at: string;
  };
  prediction: PredictionResult | null;
  shap: ExplanationResult | null;
  lime: ExplanationResult | null;
  comparison: ComparisonResult | null;
  counterfactual: CounterfactualResult | null;
}

export interface ModelMetadata {
  final_model: string;
  trained_at: string;
  dataset_size: number;
  train_size: number;
  test_size: number;
  feature_columns: string[];
  target_column: string;
  protected_attribute: string;
  model_comparison: Record<string, {
    accuracy: number; precision: number; recall: number; f1: number; roc_auc?: number;
    confusion_matrix: number[][];
  }>;
}

export interface GlobalShapEntry {
  feature: string;
  label: string;
  mean_abs_shap: number;
}

export interface FairnessReport {
  protected_attribute: string;
  protected_attribute_caveat: string;
  group_metrics: Record<string, Record<string, number>>;
  overall_metrics: { accuracy: number; selection_rate: number };
  disparity_metrics: { demographic_parity_difference: number; equalized_odds_difference: number };
  interpretation: string[];
  sample_size: number;
  disclaimer: string;
}

export interface ApplicationsSummary {
  total: number;
  approved: number;
  rejected: number;
  approval_rate: number | null;
}
