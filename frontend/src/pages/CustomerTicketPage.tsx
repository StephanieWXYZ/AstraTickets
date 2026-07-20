import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import {
  ApiError,
  createTicketReply,
  getTicket,
  listTicketReplies,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, TicketReply } from "../types";

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

export function CustomerTicketPage() {
  const { ticketId } = useParams();
  const { user, token, signOut } = useAuth();
  const numericTicketId = Number(ticketId);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [replies, setReplies] = useState<TicketReply[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reply, setReply] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [replyError, setReplyError] = useState("");

  const loadConversation = useCallback(async () => {
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
    } catch (error) {
      setLoadError(
        error instanceof ApiError
          ? error.message
          : "We could not load this conversation. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [numericTicketId, token]);

  useEffect(() => {
    void loadConversation();
  }, [loadConversation]);

  async function handleReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !ticket) return;
    setIsSubmitting(true);
    setReplyError("");
    try {
      const createdReply = await createTicketReply(token, ticket.id, reply);
      setReplies((current) => [...current, createdReply]);
      setReply("");
      if (ticket.status === "resolved") {
        setTicket({
          ...ticket,
          status: ticket.assignee_id === null ? "open" : "in_progress",
          resolved_at: null,
        });
      }
    } catch (error) {
      setReplyError(
        error instanceof ApiError
          ? error.message
          : "We could not send your reply. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="workspace conversation-workspace">
      <header className="workspace-header">
        <Link className="brand" to="/customer/dashboard">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>AstraTickets</span>
        </Link>
        <div className="account-actions">
          <span className="account-name">{user?.full_name}</span>
          <button className="button button-quiet" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <div className="conversation-shell">
        <Link className="back-link" to="/customer/dashboard">← Back to your tickets</Link>

        {isLoading ? (
          <div className="conversation-state" aria-live="polite">Opening conversation…</div>
        ) : loadError || !ticket ? (
          <div className="conversation-state" role="alert">
            <h1>We could not open this ticket</h1>
            <p>{loadError || "Ticket not found"}</p>
            <button className="text-button" type="button" onClick={() => void loadConversation()}>
              Try again
            </button>
          </div>
        ) : (
          <>
            <section className="conversation-title" aria-labelledby="ticket-title">
              <div>
                <p className="eyebrow">Ticket #{ticket.id}</p>
                <h1 id="ticket-title">{ticket.title}</h1>
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

            <div className="conversation-grid">
              <section className="panel conversation-panel" aria-label="Ticket conversation">
                <article className="message message-customer">
                  <header>
                    <div>
                      <strong>{user?.full_name}</strong>
                      <span>Customer</span>
                    </div>
                    <time dateTime={ticket.created_at}>{formatDateTime(ticket.created_at)}</time>
                  </header>
                  <p>{ticket.description}</p>
                </article>

                {replies.map((item) => {
                  const isCustomer = item.author.role === "customer";
                  return (
                    <article
                      className={`message ${isCustomer ? "message-customer" : "message-staff"}`}
                      key={item.id}
                    >
                      <header>
                        <div>
                          <strong>{item.author.full_name}</strong>
                          <span>{isCustomer ? "Customer" : "Support team"}</span>
                        </div>
                        <time dateTime={item.created_at}>{formatDateTime(item.created_at)}</time>
                      </header>
                      <p>{item.content}</p>
                    </article>
                  );
                })}

                {replies.length === 0 && (
                  <div className="awaiting-reply">
                    Your request is in the queue. The conversation will continue here.
                  </div>
                )}
              </section>

              <aside className="panel reply-panel">
                <div className="panel-heading">
                  <p className="eyebrow">Add to conversation</p>
                  <h2>Send a reply</h2>
                </div>
                {ticket.status === "closed" ? (
                  <div className="closed-notice">
                    This ticket is closed. A support team member must reopen it before anyone can reply.
                  </div>
                ) : (
                  <form onSubmit={handleReply}>
                    <label>
                      Your message
                      <textarea
                        required
                        maxLength={5000}
                        rows={7}
                        value={reply}
                        onChange={(event) => setReply(event.target.value)}
                        placeholder="Share an update or answer a question from support."
                      />
                    </label>
                    {ticket.status === "resolved" && (
                      <p className="reply-note">
                        Sending a reply will reopen this ticket so the support team can help again.
                      </p>
                    )}
                    {replyError && <div className="form-error" role="alert">{replyError}</div>}
                    <button className="button button-primary" type="submit" disabled={isSubmitting}>
                      {isSubmitting ? "Sending reply…" : "Send reply"}
                    </button>
                  </form>
                )}
              </aside>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
