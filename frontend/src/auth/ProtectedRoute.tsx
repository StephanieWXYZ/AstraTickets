import { Navigate, Outlet, useLocation } from "react-router-dom";

import type { UserRole } from "../types";
import { useAuth } from "./AuthContext";

export function dashboardPath(role: UserRole): string {
  return role === "customer" ? "/customer/dashboard" : "/staff/dashboard";
}

export function ProtectedRoute({ allowedRoles }: { allowedRoles: UserRole[] }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="page-loading">Opening your workspace…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={dashboardPath(user.role)} replace />;
  }
  return <Outlet />;
}
