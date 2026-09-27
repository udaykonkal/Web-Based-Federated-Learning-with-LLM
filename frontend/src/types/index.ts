export type UserRole = 'admin' | 'client';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  client_id: string | null;
  is_active: boolean;
}

export interface Client {
  id: string; // 'client_1', 'client_2', 'client_3'
  name: string; // 'Hospital/Clinic A', etc.
  institution_type: string;
  location: string | null;
  status: string;
  created_at: string;
  last_seen: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  client_id: string | null;
  institution_name: string | null;
  email: string;
}

export interface MLModel {
  id: number;
  name: string;
  healthcare_task: 'diabetes_prediction' | 'heart_disease_prediction';
  description: string;
  architecture: string;
  version: string;
  status: 'draft' | 'uploaded' | 'published' | 'active' | 'inactive' | 'archived';
  target_variable: string;
  fl_enabled: boolean;
}

export interface Dataset {
  id: number;
  name: string;
  healthcare_task: 'diabetes_prediction' | 'heart_disease_prediction';
  filename: string;
  record_count: number;
  feature_count: number;
  target_variable: string;
  class_distribution: Record<string, number>;
  feature_names: string[];
  status: 'active' | 'inactive';
  is_admin_managed: boolean;
  is_distributed: boolean;
  distributed_at: string | null;
  created_at: string;
  disclaimer: string;
  summary_stats?: Record<string, { mean: number; std: number; min: number; max: number }>;
}


export interface ClientPrivateProfile {
  client_id: string;
  institution_name: string;
  diabetes_samples: number;
  diabetes_features: number;
  heart_disease_samples: number;
  heart_disease_features: number;
  privacy_status: string;
}

export interface AdminHealthStats {
  status: string;
  role: string;
  coordinator: string;
  active_clients: number;
  datasets_count: number;
  models_count: number;
  experiments_count: number;
}
