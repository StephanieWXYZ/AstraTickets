import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { dashboardPath } from "../auth/ProtectedRoute";
import { AuthShell } from "../components/AuthShell";

export function RegisterPage() {
  const { user, signUp } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
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
      const currentUser = await signUp({
        email,
        password,
        full_name: fullName,
      });
      navigate(dashboardPath(currentUser.role), { replace: true });
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not create your account. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <div className="form-card">
        <div className="form-heading">
          <p className="eyebrow">Customer access</p>
          <h2>Create your account</h2>
          <p>Start a secure support conversation with the team.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              minLength={1}
              maxLength={120}
              required
            />
          </label>
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
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              maxLength={128}
              aria-describedby="password-help"
              required
            />
            <span id="password-help" className="field-help">Use at least 8 characters.</span>
          </label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary" type="submit" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="form-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </AuthShell>
  );
}
