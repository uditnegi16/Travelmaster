import { BrowserRouter, Routes, Route, Navigate, Link, Outlet } from "react-router-dom";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  useAuth,
} from "@clerk/clerk-react";
import Trips from "./app/routes/Trip";

import ProtectedRoute from "./app/layout/ProtectedRoute";
import AppShell from "./app/layout/AppShell";
import TripNew from "./app/routes/TripNew";

import Dashboard from "./app/routes/Dashboard";
import Saved from "./app/routes/Saved";
import Account from "./app/routes/Account";
import SessionDetail from "./app/routes/SessionDetail";
import LandingPage from "./app/routes/Landing";
import NotFound from "./app/routes/NotFound";

function AfterLoginLanding() {
  const { isSignedIn, isLoaded } = useAuth();

  // Avoid flicker while Clerk loads
  if (!isLoaded) return null;

  // If user is not signed in, they should never see this page
  if (!isSignedIn) {
    return <Navigate to="/" replace />;
  }

  // Signed in: show your post-login UI
  return (
    <div className="min-h-screen bg-[#060913] text-slate-100">
      <header className="border-b border-white/10">
        <div className="container-page flex items-center justify-between py-5">
          <Link to="/" className="font-extrabold text-lg">TravelGuru</Link>

          <SignedIn>
            <Link to="/app/dashboard" className="btn btn-primary">Open App</Link>
          </SignedIn>
        </div>
      </header>

      <main className="container-page py-14">
        <div className="card p-8 md:p-12">
          <h1 className="text-4xl md:text-5xl font-extrabold leading-tight">
            Welcome to TravelGuru
          </h1>
          <p className="muted mt-4 max-w-2xl">
            Phase-1 is DB-only: dashboard, sessions, saved trips, and account. Agent chat comes later.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/app/dashboard" className="btn btn-primary">Go to dashboard</Link>
            <Link to="/app/account" className="btn">Account</Link>
            <Link to="/app/saved" className="btn">Saved Trips</Link>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public landing page */}
        <Route path="/" element={<LandingPage />} />

        {/* After-login landing page */}
        <Route path="/welcome" element={<AfterLoginLanding />} />

        {/* Protected app */}
        <Route path="/app" element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="dashboard" element={<Dashboard />} />

            <Route path="trips" element={<Trips />} />
            <Route path="trips/new" element={<TripNew />} />

            <Route path="saved" element={<Saved />} />
            <Route path="account" element={<Account />} />

            <Route path="sessions/:id" element={<SessionDetail />} />

            <Route index element={<Navigate to="dashboard" replace />} />

          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
