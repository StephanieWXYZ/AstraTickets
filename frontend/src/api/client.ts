import type {
  CreateTicketInput,
  RegisterInput,
  Ticket,
  TicketPage,
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

export function listTickets(token: string): Promise<TicketPage> {
  return request<TicketPage>("/api/tickets?limit=100", {
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
