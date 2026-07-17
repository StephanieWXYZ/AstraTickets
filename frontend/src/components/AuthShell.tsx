import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <main className="auth-layout">
      <section className="auth-story" aria-label="AstraTickets introduction">
        <Link to="/" className="brand brand-light" aria-label="AstraTickets home">
          <span className="brand-mark">A</span>
          <span>AstraTickets</span>
        </Link>
        <div className="story-copy">
          <p className="eyebrow">Support that stays grounded</p>
          <h1>Every customer question, handled with clarity.</h1>
          <p>
            Bring customer conversations, accountable workflows, and
            knowledge-backed assistance into one calm workspace.
          </p>
        </div>
        <div className="trust-note">
          <span className="status-dot" />
          AI suggestions stay in draft until a support agent approves them.
        </div>
      </section>
      <section className="auth-panel">{children}</section>
    </main>
  );
}
