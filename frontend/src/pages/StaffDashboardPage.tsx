import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, assignTicket, listTickets } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, TicketPriority, TicketStatus } from "../types";

type StatusFilter = "all" | TicketStatus;
type PriorityFilter = "all" | TicketPriority;

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

export function StaffDashboardPage() {
  const { user, token, signOut } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [workingTicketId, setWorkingTicketId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");

  const loadQueue = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setLoadError("");
    try {
      const page = await listTickets(token);
      setTickets(page.items);
    } catch (error) {
      setLoadError(
        error instanceof ApiError
          ? error.message
          : "We could not load the support queue. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  const visibleTickets = useMemo(
    () =>
      tickets.filter(
        (ticket) =>
          (statusFilter === "all" || ticket.status === statusFilter) &&
          (priorityFilter === "all" || ticket.priority === priorityFilter),
      ),
    [priorityFilter, statusFilter, tickets],
  );

  const unassignedCount = tickets.filter(
    (ticket) =>
      ticket.assignee_id === null &&
      ticket.status !== "resolved" &&
      ticket.status !== "closed",
  ).length;
  const myTicketCount = tickets.filter(
    (ticket) => ticket.assignee_id === user?.id,
  ).length;
  const urgentCount = tickets.filter(
    (ticket) =>
      ticket.priority === "urgent" &&
      ticket.status !== "resolved" &&
      ticket.status !== "closed",
  ).length;

  async function updateAssignment(ticket: Ticket, assigneeId: number | null) {
    if (!token) return;
    setWorkingTicketId(ticket.id);
    setActionError("");
    try {
      const updatedTicket = await assignTicket(token, ticket.id, assigneeId);
      setTickets((current) =>
        current.map((item) => (item.id === updatedTicket.id ? updatedTicket : item)),
      );
    } catch (error) {
      setActionError(
        error instanceof ApiError
          ? error.message
          : "We could not update this assignment. Please try again.",
      );
    } finally {
      setWorkingTicketId(null);
    }
  }

  return (
    <main className="workspace staff-workspace">
      <header className="workspace-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>AstraTickets</span>
        </div>
        <div className="account-actions">
          <span className="account-name">{user?.full_name} · {user?.role}</span>
          <button className="button button-quiet" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <section className="staff-intro">
        <div>
          <p className="eyebrow">Support workspace</p>
          <h1>Support queue</h1>
          <p>See what needs attention and take ownership of the next request.</p>
        </div>
        <div className="queue-metrics" aria-label="Support queue summary">
          <div><strong>{unassignedCount}</strong><span>Unassigned</span></div>
          <div><strong>{myTicketCount}</strong><span>Assigned to you</span></div>
          <div><strong>{urgentCount}</strong><span>Urgent</span></div>
        </div>
      </section>

      <section className="panel queue-panel" aria-labelledby="queue-title">
        <div className="queue-toolbar">
          <div>
            <p className="eyebrow">All requests</p>
            <h2 id="queue-title">Customer tickets</h2>
          </div>
          <div className="queue-filters">
            <label>
              Status
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              >
                <option value="all">All statuses</option>
                <option value="open">Open</option>
                <option value="in_progress">In progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </label>
            <label>
              Priority
              <select
                value={priorityFilter}
                onChange={(event) => setPriorityFilter(event.target.value as PriorityFilter)}
              >
                <option value="all">All priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
          </div>
        </div>

        {actionError && <div className="queue-error" role="alert">{actionError}</div>}

        {isLoading ? (
          <div className="ticket-state" aria-live="polite">Loading the support queue…</div>
        ) : loadError ? (
          <div className="ticket-state error-state" role="alert">
            <p>{loadError}</p>
            <button className="text-button" type="button" onClick={() => void loadQueue()}>
              Try again
            </button>
          </div>
        ) : visibleTickets.length === 0 ? (
          <div className="ticket-state empty-state">
            <div className="empty-mark" aria-hidden="true">✓</div>
            <h3>No matching tickets</h3>
            <p>Change the filters to see a different part of the queue.</p>
          </div>
        ) : (
          <div className="queue-list">
            {visibleTickets.map((ticket) => {
              const isMine = ticket.assignee_id === user?.id;
              const canBeAssigned = ticket.status !== "resolved" && ticket.status !== "closed";
              return (
                <article className="queue-ticket" key={ticket.id}>
                  <div className="queue-ticket-main">
                    <div className="ticket-card-topline queue-ticket-topline">
                      <span className={`status-badge status-${ticket.status}`}>
                        {formatLabel(ticket.status)}
                      </span>
                      <span className={`priority-label priority-${ticket.priority}`}>
                        {ticket.priority} priority
                      </span>
                    </div>
                    <h3>
                      <Link to={`/staff/tickets/${ticket.id}`}>{ticket.title}</Link>
                    </h3>
                    <p>{ticket.description}</p>
                    <div className="queue-ticket-meta">
                      <span>Ticket #{ticket.id}</span>
                      <time dateTime={ticket.created_at}>{formatDate(ticket.created_at)}</time>
                      <span>
                        {ticket.assignee_id === null
                          ? "No owner"
                          : isMine
                            ? "Assigned to you"
                            : "Assigned to another teammate"}
                      </span>
                    </div>
                  </div>
                  <div className="queue-ticket-action">
                    {ticket.assignee_id === null && canBeAssigned ? (
                      <button
                        className="button button-primary"
                        type="button"
                        disabled={workingTicketId === ticket.id}
                        onClick={() => user && void updateAssignment(ticket, user.id)}
                      >
                        {workingTicketId === ticket.id ? "Claiming…" : "Claim ticket"}
                      </button>
                    ) : isMine && canBeAssigned ? (
                      <button
                        className="button button-quiet"
                        type="button"
                        disabled={workingTicketId === ticket.id}
                        onClick={() => void updateAssignment(ticket, null)}
                      >
                        {workingTicketId === ticket.id ? "Releasing…" : "Release"}
                      </button>
                    ) : (
                      <span className="assignment-label">
                        {ticket.assignee_id === null ? "Not active" : "Owned"}
                      </span>
                    )}
                    <Link className="queue-view-link" to={`/staff/tickets/${ticket.id}`}>
                      Open ticket
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
