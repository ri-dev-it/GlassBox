import axios from 'axios';
import type {
  AuthResponse, ApplicantFeatures, ApplicationDetail, ExplanationResult,
  CounterfactualResult, ModelMetadata, GlobalShapEntry, FairnessReport,
  ApplicationsSummary,
  DocumentRecord, DocumentType,
} from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  // FormData must retain the browser-generated multipart boundary. The JSON
  // default configured above is appropriate for API payloads, not uploads.
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    config.headers?.delete?.('Content-Type');
    if (config.headers && !config.headers.delete) delete (config.headers as Record<string, unknown>)['Content-Type'];
  }
  const token = localStorage.getItem('xai_loan_token');
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
}

export const healthApi = {
  check: () => api.get<HealthCheckResponse>('/health').then((r) => r.data),
};

export const authApi = {
  register: (payload: { email: string; password: string; full_name: string }) =>
    api.post<AuthResponse>('/auth/register', payload).then((r) => r.data),
  login: (payload: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', payload).then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
  me: () => api.get<{ user: AuthResponse['user'] }>('/auth/me').then((r) => r.data.user),
};

export const applicationApi = {
  submit: (features: ApplicantFeatures) =>
    api.post<ApplicationDetail>('/predict', features).then((r) => r.data),
  list: () => api.get<{ applications: ApplicationDetail['application'][] }>('/applications').then((r) => r.data.applications),
  getById: (id: number) => api.get<ApplicationDetail>(`/applications/${id}`).then((r) => r.data),
};

export const documentApi = {
  pending: () => api.get<{ documents: DocumentRecord[] }>('/documents/pending').then((r) => r.data.documents),
  upload: (documentType: DocumentType, file: File) => {
    const body = new FormData(); body.append('documentType', documentType); body.append('file', file);
    return api.post<{ document: DocumentRecord }>('/documents', body).then((r) => r.data.document);
  },
};

export const explanationApi = {
  shap: (features: ApplicantFeatures) =>
    api.post<{ prediction: unknown } & ExplanationResult>('/explain/shap', features).then((r) => r.data),
  lime: (features: ApplicantFeatures) =>
    api.post<{ prediction: unknown } & ExplanationResult>('/explain/lime', features).then((r) => r.data),
  counterfactual: (features: ApplicantFeatures) =>
    api.post<CounterfactualResult>('/explain/counterfactual', features).then((r) => r.data),
};

export const analyticsApi = {
  model: () => api.get<ModelMetadata>('/analytics/model').then((r) => r.data),
  globalShap: () => api.get<{ global_importance: GlobalShapEntry[] }>('/analytics/shap').then((r) => r.data.global_importance),
  fairness: () => api.get<FairnessReport>('/analytics/fairness').then((r) => r.data),
  applicationsSummary: () => api.get<ApplicationsSummary>('/analytics/applications-summary').then((r) => r.data),
  dashboard: () => api.get<DashboardStats>('/dashboard/stats').then((r) => r.data),
};

export interface DashboardStats {
  total: number; approved: number; rejected: number; under_review: number; approval_rate: number | null;
  risk_distribution: { low: number; medium: number; high: number };
  recent_applications: Array<import('../types').ApplicationDetail['application'] & { prediction: import('../types').PredictionResult | null }>;
}
