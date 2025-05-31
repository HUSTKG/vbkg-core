export type UserCreate = UserBase & {
  password: string;
  roles?: string[];
};

export type UserLogin = {
  email: string;
  password: string;
};

export type Token = {
  access_token: string;
  refresh_token: string;
};

export type TokenPayload = {
  sub?: string;
  exp?: number;
};

// Base Types
export interface UserBase {
  email: string;
  full_name?: string;
  department?: string;
  position?: string;
  bio?: string;
}

export interface User extends UserBase {
  id: string;
  is_active: boolean;
  roles: string[];
  permissions: string[];
  avatar_url?: string;
  last_sign_in_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserUpdate {
  full_name?: string;
  department?: string;
  position?: string;
  bio?: string;
  avatar_url?: string;
  roles?: string[];
}

export interface Role {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface Permission {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface APIKey {
  id: string;
  name: string;
  description?: string;
  key_prefix: string;
  user_id: string;
  is_active: boolean;
  expires_at?: string;
  rate_limit: number;
  allowed_ips: string[];
  last_used?: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
  token?: string; // Only returned on creation
}

export interface APIKeyCreate {
  name: string;
  description?: string;
  expires_days?: number;
  rate_limit?: number;
  allowed_ips?: string[];
}

export interface UserActivity {
  id: string;
  user_id: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface SystemStats {
  user_counts_by_role: Record<string, number>;
  active_api_keys: number;
  recent_activity_count: number;
  total_users: number;
}
