import { useAuth } from "../auth/AuthContext";

export function DashboardPlaceholder({ audience }: { audience: "customer" | "staff" }) {
  const { user, signOut } = useAuth();
  const isCustomer = audience === "customer";

  return (
    <main className="dashboard-placeholder">
      <header className="dashboard-header">
        <div className="brand">
          <span className="brand-mark">A</span>
          <span>AstraTickets</span>
        </div>
        <button className="button button-quiet" type="button" onClick={signOut}>
          Sign out
        </button>
      </header>
      <section className="welcome-card">
        <p className="eyebrow">{isCustomer ? "Customer workspace" : "Support workspace"}</p>
        <h1>Welcome, {user?.full_name}.</h1>
        <p>
          {isCustomer
            ? "Your ticket workspace is ready. Ticket creation and history are coming next."
            : "Your support queue is ready. Assignment and response tools are coming next."}
        </p>
        <div className="role-chip">Signed in as {user?.role}</div>
      </section>
    </main>
  );
}
