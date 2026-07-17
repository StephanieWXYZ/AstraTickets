import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { dashboardPath } from "../auth/ProtectedRoute";
import { useAuth } from "../auth/AuthContext";
import { AuthShell } from "../components/AuthShell";

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={dashboardPath(user.role)} replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const currentUser = await signIn(email, password);
      navigate(dashboardPath(currentUser.role), { replace: true });
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not sign you in. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <div className="form-card">
        <div className="form-heading">
          <p className="eyebrow">Welcome back</p>
          <h2>Sign in to your workspace</h2>
          <p>Use your account email and password to continue.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="form-footer">
          New customer? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </AuthShell>
  );
}
