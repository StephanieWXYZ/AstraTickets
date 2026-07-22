import type {
  CreateTicketInput,
  RegisterInput,
  Ticket,
  TicketPage,
  TicketPriority,
  TicketReply,
  TicketStatus,
  TokenResponse,
  User,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // Keep the safe fallback message when the server returns no JSON body.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username: email, password });
  return request<TokenResponse>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export function register(input: RegisterInput): Promise<User> {
  return request<User>("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function getCurrentUser(token: string): Promise<User> {
  return request<User>("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

function authorizationHeader(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export interface TicketFilters {
  status?: TicketStatus;
  priority?: TicketPriority;
}

export function listTickets(
  token: string,
  filters: TicketFilters = {},
): Promise<TicketPage> {
  const query = new URLSearchParams({ limit: "100" });
  if (filters.status) query.set("status", filters.status);
  if (filters.priority) query.set("priority", filters.priority);
  return request<TicketPage>(`/api/tickets?${query.toString()}`, {
    headers: authorizationHeader(token),
  });
}

export function createTicket(
  token: string,
  input: CreateTicketInput,
): Promise<Ticket> {
  return request<Ticket>("/api/tickets", {
    method: "POST",
    headers: {
      ...authorizationHeader(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export function getTicket(token: string, ticketId: number): Promise<Ticket> {
  return request<Ticket>(`/api/tickets/${ticketId}`, {
    headers: authorizationHeader(token),
  });
}

export function listTicketReplies(
  token: string,
  ticketId: number,
): Promise<TicketReply[]> {
  return request<TicketReply[]>(`/api/tickets/${ticketId}/replies`, {
    headers: authorizationHeader(token),
  });
}

export function createTicketReply(
  token: string,
  ticketId: number,
  content: string,
): Promise<TicketReply> {
  return request<TicketReply>(`/api/tickets/${ticketId}/replies`, {
    method: "POST",
    headers: {
      ...authorizationHeader(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  });
}

export function assignTicket(
  token: string,
  ticketId: number,
  assigneeId: number | null,
): Promise<Ticket> {
  return request<Ticket>(`/api/tickets/${ticketId}/assignment`, {
    method: "PATCH",
    headers: {
      ...authorizationHeader(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ assignee_id: assigneeId }),
  });
}

export function updateTicketStatus(
  token: string,
  ticketId: number,
  status: TicketStatus,
): Promise<Ticket> {
  return request<Ticket>(`/api/tickets/${ticketId}`, {
    method: "PATCH",
    headers: {
      ...authorizationHeader(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
}

export function listActiveStaff(token: string): Promise<User[]> {
  return request<User[]>("/api/users/staff", {
    headers: authorizationHeader(token),
  });
}
