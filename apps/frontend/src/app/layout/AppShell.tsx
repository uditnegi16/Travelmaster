import { NavLink, Outlet } from "react-router-dom";
import { SignedIn, UserButton } from "@clerk/clerk-react";

const linkBase =
  "block rounded-xl px-3 py-2 text-sm transition hover:bg-white/10";
const linkActive = "bg-white/10 border border-white/10";

export default function AppShell() {
  return (
    <div className="min-h-screen">
      {/* Topbar */}
      <header className="sticky top-0 z-20 border-b border-white/10 bg-[#060913]/80 backdrop-blur">
        <div className="container-page flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-white/10 border border-white/10" />
            <div>
              <div className="font-extrabold leading-none">TravelGuru</div>
              <div className="text-xs text-slate-300/70 leading-none mt-1">
                Travel planning dashboard
              </div>
            </div>
          </div>

            <SignedIn>
              <div className="flex items-center gap-3">
                <span className="text-xs px-3 py-1 rounded-full bg-white/10 text-white/70 border border-white/10">
                  Phase-1 • DB Mode
                </span>
                <UserButton />
              </div>
            </SignedIn>

        </div>
      </header>

      {/* Body */}
      <div className="container-page grid grid-cols-1 md:grid-cols-[260px_1fr] gap-6 py-6">
        {/* Sidebar */}
        <aside className="card p-4 h-fit md:sticky md:top-[88px]">
          <div className="text-xs uppercase tracking-wider text-slate-300/60 mb-3">
            Menu
          </div>

          <nav className="space-y-2">
            <NavLink
              to="/app/trips"
              className={({ isActive }) => `${linkBase} ${isActive ? linkActive : ""}`}
            >
              Trips
            </NavLink>
            
            <NavLink
              to="/app/dashboard"
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : ""}`
              }
            >
              Dashboard
            </NavLink>

            <NavLink
              to="/app/saved"
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : ""}`
              }
            >
              Saved Trips
            </NavLink>

            <NavLink
              to="/app/account"
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : ""}`
              }
            >
              Account
            </NavLink>
          </nav>

          <div className="mt-5 pt-4 border-t border-white/10 text-xs text-slate-300/60">
            Phase-1 (DB only). Agent integration later.
          </div>
        </aside>

        {/* Content */}
        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
