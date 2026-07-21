import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import {
  ApiError,
  assignTicket,
  createTicketReply,
  getTicket,
  listTicketReplies,
  updateTicketStatus,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, TicketReply, TicketStatus } from "../types";

const statusTransitions: Record<TicketStatus, TicketStatus[]> = {
  open: ["in_progress", "resolved", "closed"],
  in_progress: ["open", "resolved", "closed"],
  resolved: ["in_progress", "closed"],
  closed: ["open"],
};

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function StaffTicketPage() {
  const { ticketId } = useParams();
  const { user, token, signOut } = useAuth();
  const numericTicketId = Number(ticketId);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [replies, setReplies] = useState<TicketReply[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reply, setReply] = useState("");
  const [replyError, setReplyError] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [nextStatus, setNextStatus] = useState<TicketStatus | "">("");
  const [workflowError, setWorkflowError] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  const loadTicket = useCallback(async () => {
    if (!token || !Number.isInteger(numericTicketId) || numericTicketId < 1) {
      setLoadError("Ticket not found");
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setLoadError("");
    try {
      const [loadedTicket, loadedReplies] = await Promise.all([
        getTicket(token, numericTicketId),
        listTicketReplies(token, numericTicketId),
      ]);
      setTicket(loadedTicket);
      setReplies(loadedReplies);
      setNextStatus("");
    } catch (error) {
      setLoadError(
        error instanceof ApiError
          ? error.message
          : "We could not load this ticket. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [numericTicketId, token]);

  useEffect(() => {
    void loadTicket();
  }, [loadTicket]);

  const isAssignedToMe = ticket?.assignee_id === user?.id;
  const canManageWorkflow = user?.role === "admin" || isAssignedToMe;
  const canReply =
    ticket?.status !== "closed" &&
    (user?.role === "admin" || isAssignedToMe);

  async function handleReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !ticket) return;
    setIsReplying(true);
    setReplyError("");
    try {
      const createdReply = await createTicketReply(token, ticket.id, reply);
      setReplies((current) => [...current, createdReply]);
      setReply("");
    } catch (error) {
      setReplyError(
        error instanceof ApiError
          ? error.message
          : "We could not send this reply. Please try again.",
      );
    } finally {
      setIsReplying(false);
    }
  }

  async function handleAssignment(assigneeId: number | null) {
    if (!token || !ticket) return;
    setIsUpdating(true);
    setWorkflowError("");
    try {
      const updatedTicket = await assignTicket(token, ticket.id, assigneeId);
      setTicket(updatedTicket);
      setNextStatus("");
    } catch (error) {
      setWorkflowError(
        error instanceof ApiError
          ? error.message
          : "We could not update the assignment. Please try again.",
      );
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleStatusUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !ticket || !nextStatus) return;
    setIsUpdating(true);
    setWorkflowError("");
    try {
      const updatedTicket = await updateTicketStatus(token, ticket.id, nextStatus);
      setTicket(updatedTicket);
      setNextStatus("");
    } catch (error) {
      setWorkflowError(
        error instanceof ApiError
          ? error.message
          : "We could not update the ticket status. Please try again.",
      );
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <main className="workspace conversation-workspace staff-ticket-workspace">
      <header className="workspace-header">
        <Link className="brand" to="/staff/dashboard">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>AstraTickets</span>
        </Link>
        <div className="account-actions">
          <span className="account-name">{user?.full_name} · {user?.role}</span>
          <button className="button button-quiet" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <div className="conversation-shell">
        <Link className="back-link" to="/staff/dashboard">← Back to support queue</Link>

        {isLoading ? (
          <div className="conversation-state" aria-live="polite">Opening ticket…</div>
        ) : loadError || !ticket ? (
          <div className="conversation-state" role="alert">
            <h1>We could not open this ticket</h1>
            <p>{loadError || "Ticket not found"}</p>
            <button className="text-button" type="button" onClick={() => void loadTicket()}>
              Try again
            </button>
          </div>
        ) : (
          <>
            <section className="conversation-title" aria-labelledby="staff-ticket-title">
              <div>
                <p className="eyebrow">Ticket #{ticket.id}</p>
                <h1 id="staff-ticket-title">{ticket.title}</h1>
              </div>
              <div className="ticket-summary-badges">
                <span className={`status-badge status-${ticket.status}`}>
                  {formatLabel(ticket.status)}
                </span>
                <span className={`priority-label priority-${ticket.priority}`}>
                  {ticket.priority} priority
                </span>
              </div>
            </section>

            <div className="staff-ticket-grid">
              <section className="panel conversation-panel" aria-label="Customer conversation">
                <article className="message message-customer">
                  <header>
                    <div><strong>Customer request</strong><span>Customer</span></div>
                    <time dateTime={ticket.created_at}>{formatDateTime(ticket.created_at)}</time>
                  </header>
                  <p>{ticket.description}</p>
                </article>

                {replies.map((item) => {
                  const fromCustomer = item.author.role === "customer";
                  return (
                    <article
                      className={`message ${fromCustomer ? "message-customer" : "message-staff"}`}
                      key={item.id}
                    >
                      <header>
                        <div>
                          <strong>{item.author.full_name}</strong>
                          <span>{fromCustomer ? "Customer" : "Support team"}</span>
                        </div>
                        <time dateTime={item.created_at}>{formatDateTime(item.created_at)}</time>
                      </header>
                      <p>{item.content}</p>
                    </article>
                  );
                })}

                <div className="staff-reply-area">
                  {canReply ? (
                    <form onSubmit={handleReply}>
                      <label>
                        Reply to customer
                        <textarea
                          required
                          maxLength={5000}
                          rows={6}
                          value={reply}
                          onChange={(event) => setReply(event.target.value)}
                          placeholder="Write a clear, helpful response."
                        />
                      </label>
                      {replyError && <div className="form-error" role="alert">{replyError}</div>}
                      <button className="button button-primary" type="submit" disabled={isReplying}>
                        {isReplying ? "Sending reply…" : "Send reply"}
                      </button>
                    </form>
                  ) : (
                    <div className="closed-notice">
                      {ticket.status === "closed"
                        ? "Reopen this ticket before replying."
                        : "Claim this ticket before replying to the customer."}
                    </div>
                  )}
                </div>
              </section>

              <aside className="panel workflow-panel" aria-labelledby="workflow-title">
                <div className="panel-heading">
                  <p className="eyebrow">Ticket controls</p>
                  <h2 id="workflow-title">Workflow</h2>
                </div>

                <dl className="ticket-facts">
                  <div><dt>Created</dt><dd>{formatDateTime(ticket.created_at)}</dd></div>
                  <div><dt>Priority</dt><dd>{formatLabel(ticket.priority)}</dd></div>
                  <div>
                    <dt>Assignment</dt>
                    <dd>
                      {ticket.assignee_id === null
                        ? "Unassigned"
                        : isAssignedToMe
                          ? "Assigned to you"
                          : "Assigned to another teammate"}
                    </dd>
                  </div>
                </dl>

                {workflowError && <div className="form-error" role="alert">{workflowError}</div>}

                <div className="assignment-controls">
                  {ticket.assignee_id === null && ticket.status !== "resolved" && ticket.status !== "closed" && (
                    <button
                      className="button button-primary"
                      type="button"
                      disabled={isUpdating}
                      onClick={() => user && void handleAssignment(user.id)}
                    >
                      Claim ticket
                    </button>
                  )}
                  {isAssignedToMe && ticket.status !== "resolved" && ticket.status !== "closed" && (
                    <button
                      className="button button-quiet"
                      type="button"
                      disabled={isUpdating}
                      onClick={() => void handleAssignment(null)}
                    >
                      Release ticket
                    </button>
                  )}
                </div>

                {canManageWorkflow ? (
                  <form className="status-form" onSubmit={handleStatusUpdate}>
                    <label>
                      Change status
                      <select
                        required
                        value={nextStatus}
                        onChange={(event) => setNextStatus(event.target.value as TicketStatus | "")}
                      >
                        <option value="">Choose next status</option>
                        {statusTransitions[ticket.status].map((status) => (
                          <option value={status} key={status}>{formatLabel(status)}</option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="button button-quiet"
                      type="submit"
                      disabled={isUpdating || nextStatus === ""}
                    >
                      {isUpdating ? "Updating…" : "Update status"}
                    </button>
                  </form>
                ) : (
                  <p className="workflow-note">Only the assigned agent or an administrator can change status.</p>
                )}
              </aside>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
