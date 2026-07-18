import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./auth/ProtectedRoute";
import { DashboardPlaceholder } from "./components/DashboardPlaceholder";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { CustomerDashboardPage } from "./pages/CustomerDashboardPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute allowedRoles={["customer"]} />}>
        <Route
          path="/customer/dashboard"
          element={<CustomerDashboardPage />}
        />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["agent", "admin"]} />}>
        <Route
          path="/staff/dashboard"
          element={<DashboardPlaceholder audience="staff" />}
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
