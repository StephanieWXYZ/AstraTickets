import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./auth/ProtectedRoute";
import { CustomerDashboardPage } from "./pages/CustomerDashboardPage";
import { CustomerTicketPage } from "./pages/CustomerTicketPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { StaffDashboardPage } from "./pages/StaffDashboardPage";
import { StaffTicketPage } from "./pages/StaffTicketPage";

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
        <Route path="/customer/tickets/:ticketId" element={<CustomerTicketPage />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["agent", "admin"]} />}>
        <Route
          path="/staff/dashboard"
          element={<StaffDashboardPage />}
        />
        <Route path="/staff/tickets/:ticketId" element={<StaffTicketPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
