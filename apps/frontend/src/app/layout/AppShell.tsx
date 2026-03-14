import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { SignedIn, UserButton, useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";

const IconCompass = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <circle cx="12" cy="12" r="10" />
    <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
  </svg>
);
const IconGrid = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);
const IconBookmark = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);
const IconUser = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);
const IconPlus = () => (
  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const IconShield = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const NAV = [
  { to: "/app/trips",     label: "Trips",       Icon: IconCompass },
  { to: "/app/dashboard", label: "Dashboard",   Icon: IconGrid },
  { to: "/app/saved",     label: "Saved Trips", Icon: IconBookmark },
  { to: "/app/account",   label: "Account",     Icon: IconUser },
];

export default function AppShell() {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        const res = await fetch("http://127.0.0.1:8000/admin/analytics", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setIsAdmin(res.ok);
      } catch {
        setIsAdmin(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen" style={{ background: "var(--bg-base)" }}>
      {/* Topbar */}
      <header className="sticky top-0 z-30 border-b"
        style={{ borderColor: "var(--border)", background: "rgba(8,12,20,0.9)", backdropFilter: "blur(20px)" }}>
        <div className="container-page flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl"
              style={{ background: "linear-gradient(135deg, var(--teal) 0%, var(--indigo) 100%)" }}>
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#080c14" strokeWidth={2.5}>
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <div>
              <div className="font-display font-bold text-base leading-none" style={{ color: "var(--text-primary)" }}>TravelGuru</div>
              <div className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>AI Travel Planner</div>
            </div>
          </div>

          <SignedIn>
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{ background: "rgba(14,196,168,0.1)", color: "var(--teal)", border: "1px solid rgba(14,196,168,0.2)" }}>
                <span className="h-1.5 w-1.5 rounded-full inline-block" style={{ background: "var(--teal)", boxShadow: "0 0 6px var(--teal)" }} />
                Live
              </div>
              <button className="btn btn-primary py-2 text-xs hidden sm:inline-flex" onClick={() => navigate("/app/trips/new")}>
                <IconPlus /> New Trip
              </button>
              <UserButton />
            </div>
          </SignedIn>
        </div>
      </header>

      {/* Body */}
      <div className="container-page grid grid-cols-1 md:grid-cols-[220px_1fr] gap-6 py-6">
        {/* Sidebar */}
        <aside className="h-fit md:sticky md:top-[65px] space-y-3">
          <div className="card p-3">
            <div className="px-2 pb-2">
              <span className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: "var(--text-muted)" }}>Menu</span>
            </div>
            <nav className="space-y-0.5">
              {NAV.map(({ to, label, Icon }) => (
                <NavLink key={to} to={to}
                  className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
                  <Icon /><span>{label}</span>
                </NavLink>
              ))}
            </nav>
            <div className="mt-2 pt-2 border-t" style={{ borderColor: "var(--border)" }}>
              <button className="nav-link w-full text-left" style={{ color: "var(--teal)" }}
                onClick={() => navigate("/app/trips/new")}>
                <IconPlus /><span>New Trip</span>
              </button>
            </div>

            {/* Admin link — only visible to admins */}
            {isAdmin && (
              <div className="mt-2 pt-2 border-t" style={{ borderColor: "var(--border)" }}>
                <button
                  className="nav-link w-full text-left"
                  style={{ color: "#f87171" }}
                  onClick={() => navigate("/admin/dashboard")}
                >
                  <IconShield /><span>Admin Panel</span>
                </button>
              </div>
            )}
          </div>
        </aside>

        {/* Content */}
        <main className="min-w-0 fade-up">
          <Outlet />
        </main>
      </div>
    </div>
  );
}