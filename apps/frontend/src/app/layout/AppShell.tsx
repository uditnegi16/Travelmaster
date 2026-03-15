// src/app/layout/AppShell.tsx
// Light/Dark mode toggle with bulb icon in topbar

import { NavLink, Outlet, useNavigate } from "react-router-dom";
import OnboardingTour from "../../components/Onboardingtour";
import { useAuth, useUser, UserButton } from "@clerk/clerk-react";
import { useEffect, useState } from "react";

// ── Icons ─────────────────────────────────────────────────────────────────────
const IconDashboard = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);
const IconTrips = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);
const IconSaved = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);
const IconAccount = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);
const IconPremium = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M2 20h20M4 20L2 8l6 4 4-8 4 8 6-4-2 12" />
  </svg>
);
const IconShield = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const IconLogout = () => (
  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);
const IconPlus = () => (
  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const IconBell = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);
const IconChat = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);
const IconSettings = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

// ── Bulb icon for theme toggle ────────────────────────────────────────────────
const IconBulbOn = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M9 21h6M12 3a6 6 0 0 1 6 6c0 2.22-1.21 4.16-3 5.2V17H9v-2.8C7.21 13.16 6 11.22 6 9a6 6 0 0 1 6-6z" />
    <line x1="12" y1="1" x2="12" y2="2" />
    <line x1="4.22" y1="4.22" x2="4.93" y2="4.93" />
    <line x1="1" y1="12" x2="2" y2="12" />
    <line x1="19.78" y1="4.22" x2="19.07" y2="4.93" />
    <line x1="23" y1="12" x2="22" y2="12" />
  </svg>
);
const IconBulbOff = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
    <path d="M9 21h6M12 3a6 6 0 0 1 6 6c0 2.22-1.21 4.16-3 5.2V17H9v-2.8C7.21 13.16 6 11.22 6 9a6 6 0 0 1 6-6z" />
  </svg>
);

// ── Theme tokens ──────────────────────────────────────────────────────────────
export default function AppShell() {
  const navigate = useNavigate();
  const { getToken, signOut } = useAuth();
  const { user } = useUser();
  const [isAdmin, setIsAdmin] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("tg-theme") === "dark";
    }
    return false;
  });

  // Persist + apply theme to body
  useEffect(() => {
    localStorage.setItem("tg-theme", dark ? "dark" : "light");
    // Apply data-theme to root so all CSS vars update
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    document.body.style.background = "";
  }, [dark]);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        const res = await fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/admin/analytics`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setIsAdmin(res.ok);
      } catch { setIsAdmin(false); }
    })();
  }, []);

  const navStyle = (isActive: boolean) => ({
    display: "flex", alignItems: "center", gap: 12,
    padding: "10px 12px", borderRadius: 10,
    fontSize: 14, fontWeight: isActive ? 600 : 400,
    textDecoration: "none", transition: "all 0.15s",
    background: isActive ? "var(--purple-light)" : "transparent",
    color: isActive ? "var(--purple)" : "var(--text-secondary)",
    border: isActive ? "1.5px solid var(--purple-glow,rgba(124,58,237,0.2))" : "1.5px solid transparent",
  });

  const Sidebar = () => (
    <div style={{
      width: 240, minWidth: 240, height: "100vh",
      background: "var(--bg-card)",
      display: "flex", flexDirection: "column",
      position: "sticky", top: 0, flexShrink: 0,
      borderRight: "1px solid var(--border)",
      overflowY: "auto",
      transition: "background 0.3s, border-color 0.3s",
    }}>
      {/* Logo + Welcome */}
      <div style={{ padding: "24px 20px 20px" }} data-tour="logo">
        {/* Logo mark */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          {/* Compass rose icon */}
          <div style={{
            width: 36, height: 36, borderRadius: 10, flexShrink: 0,
            background: "linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 12px rgba(124,58,237,0.35)",
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              {/* Compass circle */}
              <circle cx="12" cy="12" r="9" stroke="rgba(255,255,255,0.3)" strokeWidth="1.2"/>
              {/* North needle — white */}
              <path d="M12 3 L14 12 L12 10 L10 12 Z" fill="white"/>
              {/* South needle — translucent */}
              <path d="M12 21 L10 12 L12 14 L14 12 Z" fill="rgba(255,255,255,0.45)"/>
              {/* Centre dot */}
              <circle cx="12" cy="12" r="1.5" fill="white"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.02em", lineHeight: 1 }}>
              TravelGuru
            </div>
            <div style={{ fontSize: 10, fontWeight: 600, color: "var(--purple)", letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 2 }}>
              AI Planner
            </div>
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "var(--border)", marginBottom: 16 }} />

        {/* Welcome text */}
        <h2 style={{ fontFamily: "Syne, sans-serif", fontSize: 22, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.2, margin: 0 }}>
          Welcome<br />Back, {user?.firstName || "Traveler"}!
        </h2>
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6, lineHeight: 1.5 }}>
          Plan your next adventure with AI
        </p>
      </div>

      {/* Nav */}
      <div style={{ flex: 1, padding: "0 14px" }}>
        <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint,#bbb)", padding: "0 8px", marginBottom: 8 }}>
          Home
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 24 }}>
          {[
            { to: "/app/dashboard", label: "Dashboard", Icon: IconDashboard, tour: "nav-dashboard" },
            { to: "/app/trips",     label: "My Trips",  Icon: IconTrips,  tour: "nav-trips" },
          ].map(({ to, label, Icon, tour }: any) => (
            <NavLink key={to} to={to} onClick={() => setMobileOpen(false)}
              data-tour={tour}
              style={({ isActive }) => navStyle(isActive)}>
              {({ isActive }) => (
                <>
                  <span style={{ color: isActive ? "var(--purple)" : "var(--text-muted)", flexShrink: 0 }}><Icon /></span>
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>

        <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint,#bbb)", padding: "0 8px", marginBottom: 8 }}>
          My TravelGuru
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 24 }}>
          {[
            { to: "/app/saved",   label: "Saved Trips", Icon: IconSaved,   tour: "nav-saved" },
            { to: "/app/account", label: "Account",     Icon: IconAccount, tour: "nav-account" },
            { to: "/app/premium", label: "Premium",     Icon: IconPremium, tour: "nav-premium" },
          ].map(({ to, label, Icon, tour }: any) => (
            <NavLink key={to} to={to} onClick={() => setMobileOpen(false)}
              data-tour={tour}
              style={({ isActive }) => navStyle(isActive)}>
              {({ isActive }) => (
                <>
                  <span style={{ color: isActive ? "var(--purple)" : "var(--text-muted)", flexShrink: 0 }}><Icon /></span>
                  <span style={{ flex: 1 }}>{label}</span>
                  {label === "Premium" && (
                    <span style={{ fontSize: 9, fontWeight: 700, background: "rgba(124,58,237,0.12)", color: "var(--purple)", padding: "2px 7px", borderRadius: 10 }}>PRO</span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>

        {isAdmin && (
          <>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint,#bbb)", padding: "0 8px", marginBottom: 8 }}>
              Admin
            </div>
            <button onClick={() => { navigate("/admin/dashboard"); setMobileOpen(false); }}
              style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", borderRadius: 10, width: "100%", background: "transparent", color: "var(--coral)", fontSize: 14, border: "1.5px solid transparent", cursor: "pointer" }}
              onMouseEnter={e => { e.currentTarget.style.background = dark ? "rgba(248,113,113,0.08)" : "rgba(239,68,68,0.05)"; e.currentTarget.style.borderColor = "var(--coral)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "transparent"; }}
            >
              <IconShield /><span>Admin Panel</span>
            </button>
          </>
        )}
      </div>


    </div>
  );

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "var(--bg-base)", transition: "background 0.3s" }}>

      {/* Desktop sidebar */}
      <div className="hidden md:flex" style={{ height: "100vh" }}>
        <Sidebar />
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="md:hidden" style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex" }} onClick={() => setMobileOpen(false)}>
          <div onClick={e => e.stopPropagation()}><Sidebar /></div>
          <div style={{ flex: 1, background: "rgba(0,0,0,0.4)" }} />
        </div>
      )}

      {/* Right */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden", width: 0 }}>

        {/* Topbar */}
        <header style={{
          height: 64, flexShrink: 0,
          background: "var(--bg-card)",
          borderBottom: "1px solid var(--border)",
          display: "flex", alignItems: "center",
          padding: "0 28px", gap: 16,
          maxWidth: 1290,
          transition: "background 0.3s, border-color 0.3s",
        }}>
          {/* Mobile menu */}
          <button className="md:hidden" onClick={() => setMobileOpen(true)}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          {/* Search */}
          <div data-tour="topbar-search" style={{ flex: 1, maxWidth: 420, display: "flex", alignItems: "center", gap: 10, background: "var(--bg-elevated)", borderRadius: 12, padding: "8px 14px", border: "1px solid var(--border)" }}>
            <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="var(--text-muted)" strokeWidth={2}>
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input placeholder="Search destinations, trips..."
              style={{ border: "none", background: "none", outline: "none", fontSize: 13, color: "var(--text-primary)", flex: 1, fontFamily: "DM Sans, sans-serif" }} />
          </div>

          {/* Search btn */}
          <button style={{ width: 36, height: 36, borderRadius: "50%", background: "#7c3aed", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#fff" strokeWidth={2.5}>
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>

          <div style={{ flex: 1 }} />

          {/* Right icons */}
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {[IconBell, IconChat, IconSettings].map((Icon, i) => (
              <button key={i}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 7, borderRadius: 8, transition: "background 0.15s" }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-elevated)")}
                onMouseLeave={e => (e.currentTarget.style.background = "none")}>
                <Icon />
              </button>
            ))}

            <div style={{ width: 1, height: 20, background: "var(--border)", margin: "0 4px" }} />

            {/* ── THEME TOGGLE BULB ── */}
            <button
              data-tour="theme-toggle"
              onClick={() => setDark(d => !d)}
              title={dark ? "Switch to Light Mode" : "Switch to Dark Mode"}
              style={{
                background: dark ? "rgba(124,58,237,0.15)" : "rgba(124,58,237,0.08)",
                border: `1px solid ${dark ? "rgba(124,58,237,0.3)" : "rgba(124,58,237,0.15)"}`,
                cursor: "pointer",
                color: dark ? "#c4b5fd" : "#7c3aed",
                padding: "6px 10px",
                borderRadius: 10,
                display: "flex", alignItems: "center", gap: 6,
                fontSize: 11, fontWeight: 600,
                transition: "all 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = dark ? "rgba(124,58,237,0.25)" : "rgba(124,58,237,0.14)")}
              onMouseLeave={e => (e.currentTarget.style.background = dark ? "rgba(124,58,237,0.15)" : "rgba(124,58,237,0.08)")}
            >
              {dark ? <IconBulbOn /> : <IconBulbOff />}
              <span className="hidden sm:inline">{dark ? "Light" : "Dark"}</span>
            </button>

            {/* Tour button */}
            <button
              data-tour="tour-btn"
              onClick={() => setShowTour(true)}
              title="Take a tour"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                cursor: "pointer",
                color: "var(--text-secondary)",
                padding: "6px 10px",
                borderRadius: 10,
                display: "flex", alignItems: "center", gap: 6,
                fontSize: 11, fontWeight: 600,
                transition: "all 0.2s",
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--purple)")}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
            >
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
              </svg>
              <span className="hidden sm:inline">Tour</span>
            </button>

            <div style={{ width: 1, height: 20, background: "var(--border)", margin: "0 4px" }} />

            <div style={{ position: "relative", zIndex: 100 }}>
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </header>

        {/* Content */}
        <main style={{ flex: 1, overflowY: "auto", overflowX: "hidden", background: "var(--bg-base)", transition: "background 0.3s" }}>
          <div style={{ padding: "28px", maxWidth: 1290 }}>
            <Outlet />
          </div>
        </main>
      {/* Onboarding tour */}
      {showTour && <OnboardingTour onDone={() => setShowTour(false)} />}
      </div>
    </div>
  );
}