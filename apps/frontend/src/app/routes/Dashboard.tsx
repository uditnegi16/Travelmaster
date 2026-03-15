// src/app/routes/Dashboard.tsx
// Light mode — Lasodo style: white cards, black text, purple accent only

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet } from "../../lib/api";
import { useNavigate } from "react-router-dom";

type UserProfile = {
  account_id: string;
  clerk_user_id: string;
  name?: string | null;
  email?: string | null;
  tier?: string | null;
  searches_this_month?: number | null;
  created_at?: string;
};
type SearchSession = {
  search_id: string;
  from_location: string;
  to_location: string;
  start_date: string;
  end_date?: string | null;
  budget?: number | null;
  session_title?: string | null;
  agent_status?: string | null;
  created_at?: string;
};
type Analytics = {
  total_trips: number;
  average_budget: number;
  most_visited_destination: string | null;
  most_visited_count: number;
  upcoming_trips: number;
};

function useCountUp(target: number, ms = 900) {
  const [v, setV] = useState(0);
  useEffect(() => {
    const n = Number.isFinite(target) ? target : 0;
    if (!n) { setV(0); return; }
    const t0 = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / ms);
      setV(Math.round(n * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return v;
}

function StatusPill({ status }: { status?: string | null }) {
  if (!status) return null;
  const s = status.toLowerCase();
  const [bg, color] = s.includes("success") || s.includes("done") || s.includes("complete")
    ? ["rgba(16,185,129,0.1)", "#059669"]
    : s.includes("active") || s.includes("running")
    ? ["rgba(99,102,241,0.1)", "#4f46e5"]
    : s.includes("fail") || s.includes("error")
    ? ["rgba(239,68,68,0.1)", "#dc2626"]
    : ["rgba(0,0,0,0.05)", "#666"];
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 20,
      background: bg, color, border: `1px solid ${color}22`,
    }}>{status}</span>
  );
}

const DESTINATIONS = [
  { city: "Bali", country: "Indonesia", price: "₹19,600", img: "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=400&q=80" },
  { city: "Manali", country: "India", price: "₹8,200", img: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&q=80" },
  { city: "Santorini", country: "Greece", price: "₹42,000", img: "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=400&q=80" },
  { city: "Dubai", country: "UAE", price: "₹21,700", img: "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400&q=80" },
];

export default function Dashboard() {
  const { getToken, isSignedIn } = useAuth();
  const [me, setMe] = useState<UserProfile | null>(null);
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        if (!isSignedIn) return;
        const token = await getToken();
        if (!token) return;
        const [profile, sess, a] = await Promise.all([
          apiGet<UserProfile>("/me", token),
          apiGet<SearchSession[]>("/me/sessions", token),
          apiGet<Analytics>("/me/analytics", token),
        ]);
        setMe(profile); setSessions(sess || []); setAnalytics(a);
      } catch (e: any) { setErr(e?.message || "Failed to load"); }
      finally { setLoading(false); }
    })();
  }, [getToken, isSignedIn]);

  const totalTrips = useCountUp(analytics?.total_trips ?? 0);
  const avgBudget  = useCountUp(Math.round(analytics?.average_budget ?? 0));
  const upcoming   = useCountUp(analytics?.upcoming_trips ?? 0);
  const topDest    = analytics?.most_visited_destination || "—";
  const isPremium  = me?.tier === "premium";
  const searchesUsed = me?.searches_this_month ?? 0;
  const searchLimit  = isPremium ? 100 : 5;
  const usagePct     = Math.min((searchesUsed / searchLimit) * 100, 100);

  return (
    <div>

      {/* Header */}
      <div style={{ marginBottom: 24 }} className="fade-up">
        <div style={{ fontSize: 13, color: "#7c3aed", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
          Plan Recommend
        </div>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <h1 style={{ fontFamily: "Syne, sans-serif", fontSize: 32, fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>
            Explore the world with AI
          </h1>
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={() => navigate("/app/trips/new")}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "9px 20px", borderRadius: 10,
                background: "transparent", color: "#7c3aed",
                fontSize: 13, fontWeight: 600,
                border: "1.5px solid #7c3aed", cursor: "pointer",
              }}>
              + New Trip
            </button>
            {!isPremium && (
              <button
                onClick={() => navigate("/app/premium")}
                style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "9px 20px", borderRadius: 10,
                  background: "#7c3aed", color: "#fff",
                  fontSize: 13, fontWeight: 600,
                  border: "none", cursor: "pointer",
                }}>
                ✦ Upgrade
              </button>
            )}
          </div>
        </div>
      </div>

      {err && <div style={{ padding: 12, background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, color: "#dc2626", fontSize: 13, marginBottom: 16 }}>{err}</div>}

      {/* Main layout */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 260px", gap: 20, alignItems: "start" }} className="dashboard-grid">

        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }} className="fade-up-1">
            {[
              { label: "TOTAL TRIPS", value: totalTrips, sub: "Sessions created", color: "#7c3aed" },
              { label: "AVG BUDGET",  value: `₹${avgBudget.toLocaleString()}`, sub: "Per trip", color: "#d97706" },
              { label: "TOP DESTINATION", value: topDest, sub: `${analytics?.most_visited_count ?? 0} trips`, color: "#6366f1" },
              { label: "UPCOMING",    value: upcoming, sub: "Future departures", color: "#ef4444" },
            ].map(({ label, value, sub, color }) => (
              <div key={label} className="card" style={{ padding: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", marginBottom: 10 }}>
                  {label}
                </div>
                {loading
                  ? <div className="skeleton" style={{ height: 28, width: 60, marginBottom: 6 }} />
                  : <div style={{ fontSize: 28, fontWeight: 800, color, fontFamily: "Syne, sans-serif", lineHeight: 1 }}>{value}</div>
                }
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>{sub}</div>
              </div>
            ))}
          </div>

          {/* Recent trips */}
          <div className="fade-up-2">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>Recent Trips</h2>
              <button onClick={() => navigate("/app/trips")}
                style={{ fontSize: 13, color: "#7c3aed", fontWeight: 600, background: "none", border: "none", cursor: "pointer" }}>
                View all →
              </button>
            </div>

            {loading ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[1,2,3].map(i => <div key={i} className="card skeleton" style={{ height: 68 }} />)}
              </div>
            ) : sessions.length === 0 ? (
              <div className="card" style={{ padding: 40, textAlign: "center" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>✈️</div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>No trips yet</h3>
                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Plan your first AI-powered trip in seconds</p>
                <button onClick={() => navigate("/app/trips/new")}
                  style={{ marginTop: 16, padding: "9px 24px", borderRadius: 10, background: "#7c3aed", color: "#fff", fontSize: 13, fontWeight: 600, border: "none", cursor: "pointer" }}>
                  Start Planning
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {sessions.slice(0, 6).map((s, i) => (
                  <div key={s.search_id} className="card fade-up"
                    style={{ padding: "14px 18px", cursor: "pointer", animationDelay: `${i * 0.04}s`, display: "flex", alignItems: "center", gap: 14 }}
                    onClick={() => navigate(`/app/sessions/${s.search_id}`)}
                    onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "#7c3aed"; (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 16px rgba(124,58,237,0.1)"; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)"; (e.currentTarget as HTMLDivElement).style.boxShadow = "0 1px 3px rgba(0,0,0,0.06)"; }}
                  >
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: "rgba(124,58,237,0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#7c3aed" strokeWidth={2}>
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="#7c3aed" />
                      </svg>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                          {s.session_title || `${s.from_location} → ${s.to_location}`}
                        </span>
                        <StatusPill status={s.agent_status} />
                      </div>
                      <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                        {s.start_date}{s.end_date ? ` → ${s.end_date}` : ""}
                        {s.budget ? `  ·  ₹${Number(s.budget).toLocaleString()}` : ""}
                      </div>
                    </div>
                    <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="var(--text-faint,#ccc)" strokeWidth={2}>
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }} className="fade-up-3">

          {/* Usage */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Monthly Usage</span>
              <span style={{ fontSize: 10, fontWeight: 700, background: isPremium ? "rgba(124,58,237,0.1)" : "rgba(0,0,0,0.06)", color: isPremium ? "#7c3aed" : "#888", padding: "2px 8px", borderRadius: 10 }}>
                {isPremium ? "✦ Premium" : "Free"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 10 }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", fontFamily: "Syne, sans-serif" }}>{loading ? "—" : searchesUsed}</span>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>/ {searchLimit} searches</span>
            </div>
            <div style={{ height: 6, borderRadius: 10, background: "var(--bg-elevated)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${usagePct}%`, borderRadius: 10, transition: "width 1s", background: usagePct >= 100 ? "#ef4444" : "#7c3aed" }} />
            </div>
            {!isPremium && (
              <button onClick={() => navigate("/app/premium")}
                style={{ marginTop: 14, width: "100%", padding: "9px 0", borderRadius: 10, background: "rgba(124,58,237,0.08)", color: "#7c3aed", fontSize: 12, fontWeight: 600, border: "1px solid rgba(124,58,237,0.15)", cursor: "pointer" }}>
                ✦ Upgrade to Premium
              </button>
            )}
          </div>

          {/* Explore destinations */}
          <div className="card" style={{ padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>Explore</span>
              <span style={{ fontSize: 11, color: "#7c3aed", fontWeight: 600 }}>Popular</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {DESTINATIONS.map(d => (
                <button key={d.city} onClick={() => navigate("/app/trips/new")}
                  style={{ display: "flex", alignItems: "center", gap: 12, padding: "6px 8px", borderRadius: 10, background: "transparent", border: "none", cursor: "pointer", width: "100%", transition: "background 0.15s" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-elevated)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                >
                  <div style={{ width: 42, height: 42, borderRadius: 10, overflow: "hidden", flexShrink: 0 }}>
                    <img src={d.img} alt={d.city} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  </div>
                  <div style={{ flex: 1, textAlign: "left" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{d.city}</div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{d.country}</div>
                  </div>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#7c3aed" }}>{d.price}</span>
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}