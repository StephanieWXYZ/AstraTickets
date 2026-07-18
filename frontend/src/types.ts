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

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: string | null;
  requester_id: number;
  assignee_id: number | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface TicketPage {
  items: Ticket[];
  total: number;
  offset: number;
  limit: number;
}

export interface CreateTicketInput {
  title: string;
  description: string;
  priority: TicketPriority;
}
