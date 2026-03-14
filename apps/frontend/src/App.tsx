// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import ProtectedRoute from "./app/layout/ProtectedRoute";
import AppShell from "./app/layout/AppShell";
import Dashboard from "./app/routes/Dashboard";
import Trips from "./app/routes/Trip";
import TripNew from "./app/routes/TripNew";
import Saved from "./app/routes/Saved";
import Account from "./app/routes/Account";
import SessionDetail from "./app/routes/SessionDetail";
import LandingPage from "./app/routes/Landing";
import NotFound from "./app/routes/NotFound";
import ErrorBoundary from "./app/layout/ErrorBoundary";
import AdminShell from "./app/routes/admin/AdminShell";
import AdminDashboard from "./app/routes/admin/AdminDashboard";
import AdminUsers from "./app/routes/admin/AdminUsers";
import AdminHealth from "./app/routes/admin/AdminHealth";
import AdminConfig from "./app/routes/admin/AdminConfig";
import AdminAuditLog from "./app/routes/admin/AdminAuditLog";
import SharedTrip from "./app/routes/Shared_Trip";
function WelcomeRedirect() {
  const { isSignedIn, isLoaded, getToken } = useAuth();
  const [redirect, setRedirect] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    (async () => {
      try {
        const token = await getToken();
        const res = await fetch("http://127.0.0.1:8000/admin/analytics", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setRedirect(res.ok ? "/admin/dashboard" : "/app/dashboard");
      } catch {
        setRedirect("/app/dashboard");
      }
    })();
  }, [isLoaded, isSignedIn]);

  if (!isLoaded || !isSignedIn) return null;
  if (!redirect) return <div className="min-h-screen bg-black" />;
  return <Navigate to={redirect} replace />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/"        element={<LandingPage />} />
          <Route path="/welcome" element={<WelcomeRedirect />} />

          <Route path="/app" element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="dashboard"     element={<Dashboard />} />
              <Route path="trips"         element={<Trips />} />
              <Route path="trips/new"     element={<TripNew />} />
              <Route path="trips/new/:id" element={<TripNew />} />
              <Route path="saved"         element={<Saved />} />
              <Route path="account"       element={<Account />} />
              <Route path="sessions/:id"  element={<SessionDetail />} />
              <Route index               element={<Navigate to="dashboard" replace />} />
            </Route>
          </Route>

          <Route path="/admin" element={<ProtectedRoute />}>
            <Route element={<AdminShell />}>
              <Route index                element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard"     element={<AdminDashboard />} />
              <Route path="users"         element={<AdminUsers />} />
              <Route path="health"        element={<AdminHealth />} />
              <Route path="config"        element={<AdminConfig />} />
              <Route path="audit"         element={<AdminAuditLog />} />
            </Route>
          </Route>

          <Route path="/share/:token" element={<SharedTrip />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}