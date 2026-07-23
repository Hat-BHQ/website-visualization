export interface UserModule {
  code: string;
  name: string;
  role: 'admin' | 'user';
  frontend_path: string;
  permissions: string[];
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  is_superadmin: boolean;
  modules: UserModule[];
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}
