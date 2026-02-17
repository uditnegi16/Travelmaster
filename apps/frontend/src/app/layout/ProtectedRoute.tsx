// frontend/src/app/layout/ProtectedRoute.tsx
import { SignedIn, SignedOut, useAuth } from "@clerk/clerk-react";
import { Navigate, Outlet } from "react-router-dom";

export default function ProtectedRoute() {
  const { isLoaded } = useAuth();

  // Prevent route flicker while Clerk is loading
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#060913] text-slate-100 flex items-center justify-center">
        <div className="text-white/70">Loading...</div>
      </div>
    );
  }

  return (
    <>
      <SignedIn>
        <Outlet />
      </SignedIn>
      <SignedOut>
        <Navigate to="/" replace />
      </SignedOut>
    </>
  );
}
