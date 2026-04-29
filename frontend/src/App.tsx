import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "@/pages/LoginPage";
import SignupPage from "@/pages/SignupPage";
import DashboardPage from "@/pages/DashboardPage";
import TenantDashboardPage from "@/pages/TenantDashboardPage";
import PropertiesPage from "@/pages/PropertiesPage";
import PropertyDetailPage from "@/pages/PropertyDetailPage";
import BillingPage from "@/pages/BillingPage";
import BillDetailPage from "@/pages/BillDetailPage";
import VerifyEmailPage from "@/pages/VerifyEmailPage";
import AcceptInvitePage from "@/pages/AcceptInvitePage";
import ProfilePage from "@/pages/ProfilePage";
import { useAuthStore } from "@/store/auth";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.accessToken);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

function SmartDashboard() {
  const user = useAuthStore((s) => s.user);
  const role = user?.active_organization
    ? user.memberships.find(
        (m) => m.organization.id === user.active_organization?.id,
      )?.role
    : null;

  if (role === "tenant" || role === "co_tenant") {
    return <TenantDashboardPage />;
  }
  return <DashboardPage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <SmartDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/properties"
        element={
          <ProtectedRoute>
            <PropertiesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/properties/:id"
        element={
          <ProtectedRoute>
            <PropertyDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/billing"
        element={
          <ProtectedRoute>
            <BillingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/billing/:id"
        element={
          <ProtectedRoute>
            <BillDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/accept-invite/:token" element={<AcceptInvitePage />} />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
