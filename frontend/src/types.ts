export type UserRole = "customer" | "agent" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
}
