import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError, createTicket, listTickets } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, TicketPriority } from "../types";

const priorityOptions: Array<{ value: TicketPriority; label: string }> = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function CustomerDashboardPage() {
  const { user, token, signOut } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketTotal, setTicketTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TicketPriority>("medium");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const loadTickets = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setLoadError("");
    try {
      const page = await listTickets(token);
      setTickets(page.items);
      setTicketTotal(page.total);
    } catch (error) {
      setLoadError(
        error instanceof ApiError
          ? error.message
          : "We could not load your tickets. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setIsSubmitting(true);
    setFormError("");
    try {
      const ticket = await createTicket(token, { title, description, priority });
      setTickets((current) => [ticket, ...current]);
      setTicketTotal((current) => current + 1);
      setTitle("");
      setDescription("");
      setPriority("medium");
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : "We could not create your ticket. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="workspace">
      <header className="workspace-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>AstraTickets</span>
        </div>
        <div className="account-actions">
          <span className="account-name">{user?.full_name}</span>
          <button className="button button-quiet" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <section className="workspace-intro">
        <div>
          <p className="eyebrow">Customer workspace</p>
          <h1>How can we help?</h1>
          <p>Create a support ticket and follow its progress in one place.</p>
        </div>
        <div className="ticket-total" aria-label={`${ticketTotal} total tickets`}>
          <strong>{ticketTotal}</strong>
          <span>Total tickets</span>
        </div>
      </section>

      <div className="customer-grid">
        <section className="panel new-ticket-panel" aria-labelledby="new-ticket-title">
          <div className="panel-heading">
            <p className="eyebrow">New request</p>
            <h2 id="new-ticket-title">Tell us what happened</h2>
          </div>
          <form onSubmit={handleSubmit}>
            <label>
              Short title
              <input
                required
                minLength={3}
                maxLength={255}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="I cannot access my account"
              />
            </label>
            <label>
              What do you need help with?
              <textarea
                required
                minLength={10}
                maxLength={10000}
                rows={6}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Please share the details so our support team can help."
              />
              <span className="field-help">Include what you tried and what you expected to happen.</span>
            </label>
            <label>
              Priority
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value as TicketPriority)}
              >
                {priorityOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            {formError && <div className="form-error" role="alert">{formError}</div>}
            <button className="button button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Sending request…" : "Create ticket"}
            </button>
          </form>
        </section>

        <section className="panel ticket-list-panel" aria-labelledby="your-tickets-title">
          <div className="panel-heading ticket-list-heading">
            <div>
              <p className="eyebrow">Request history</p>
              <h2 id="your-tickets-title">Your tickets</h2>
            </div>
            {!isLoading && loadError && (
              <button className="text-button" type="button" onClick={() => void loadTickets()}>
                Try again
              </button>
            )}
          </div>

          {isLoading ? (
            <div className="ticket-state" aria-live="polite">Loading your tickets…</div>
          ) : loadError ? (
            <div className="ticket-state error-state" role="alert">{loadError}</div>
          ) : tickets.length === 0 ? (
            <div className="ticket-state empty-state">
              <div className="empty-mark" aria-hidden="true">✓</div>
              <h3>No tickets yet</h3>
              <p>When you ask for help, your request will appear here.</p>
            </div>
          ) : (
            <div className="ticket-list">
              {tickets.map((ticket) => (
                <article className="ticket-card" key={ticket.id}>
                  <div className="ticket-card-topline">
                    <span className={`status-badge status-${ticket.status}`}>
                      {formatLabel(ticket.status)}
                    </span>
                    <span className={`priority-label priority-${ticket.priority}`}>
                      {ticket.priority}
                    </span>
                  </div>
                  <h3>
                    <Link to={`/customer/tickets/${ticket.id}`}>{ticket.title}</Link>
                  </h3>
                  <p>{ticket.description}</p>
                  <footer>
                    <span>Ticket #{ticket.id}</span>
                    <span className="ticket-footer-action">
                      <time dateTime={ticket.created_at}>{formatDate(ticket.created_at)}</time>
                      <Link to={`/customer/tickets/${ticket.id}`}>View conversation</Link>
                    </span>
                  </footer>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
