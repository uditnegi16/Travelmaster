import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet } from "../../lib/api";
import { useNavigate } from "react-router-dom";

type UserProfile = {
  account_id: string;
  clerk_user_id: string;
  name?: string | null;
  email?: string | null;
  created_at?: string;
};

type SearchSession = {
  search_id: string;
  account_id: string;
  from_location: string;
  to_location: string;
  start_date: string;
  end_date?: string | null;
  budget?: number | null;
  created_at?: string;
  session_title?: string | null;
  agent_status?: string | null;
  data_source?: string | null;
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
    const t0 = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / ms);
      const e = 1 - Math.pow(1 - p, 3);
      setV(Math.round(n * e));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    setV(0);
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return v;
}

type StatCardProps = {
  label: string;
  value: React.ReactNode;
  sub: string;
  accent: string;
  icon: React.ReactNode;
  delay?: string;
};

function StatCard({ label, value, sub, accent, icon, delay = "0s" }: StatCardProps) {
  return (
    <div className="card p-5 fade-up" style={{ animationDelay: delay }}>
      <div className="flex items-start justify-between">
        <span className="text-xs uppercase tracking-widest font-semibold" style={{ color: "var(--text-muted)" }}>{label}</span>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: `${accent}18`, color: accent }}>
          {icon}
        </div>
      </div>
      <div className="mt-3 text-3xl font-display font-bold" style={{ color: "var(--text-primary)" }}>{value}</div>
      <div className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>{sub}</div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="card p-5">
      <div className="skeleton h-3 w-20 mb-4" />
      <div className="skeleton h-8 w-16 mb-2" />
      <div className="skeleton h-3 w-28" />
    </div>
  );
}

function statusBadge(status?: string | null) {
  if (!status) return <span className="badge badge-gray">—</span>;
  const s = status.toLowerCase();
  if (s.includes("done") || s.includes("complete") || s.includes("success"))
    return <span className="badge badge-mint">{status}</span>;
  if (s.includes("running") || s.includes("pending"))
    return <span className="badge badge-amber">{status}</span>;
  if (s.includes("fail") || s.includes("error"))
    return <span className="badge badge-coral">{status}</span>;
  return <span className="badge badge-gray">{status}</span>;
}

export default function Dashboard() {
  const { getToken, isSignedIn } = useAuth();
  const [me, setMe] = useState<UserProfile | null>(null);
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setErr("");
        if (!isSignedIn) return;
        const token = await getToken();
        if (!token) throw new Error("Missing Clerk token");
        const [profile, sess, a] = await Promise.all([
          apiGet<UserProfile>("/me", token),
          apiGet<SearchSession[]>("/me/sessions", token),
          apiGet<Analytics>("/me/analytics", token),
        ]);
        setMe(profile);
        setSessions(sess || []);
        setAnalytics(a);
      } catch (e: any) {
        setErr(e?.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken, isSignedIn]);

  const totalTrips = useCountUp(analytics?.total_trips ?? 0);
  const avgBudget  = useCountUp(Math.round(analytics?.average_budget ?? 0));
  const upcoming   = useCountUp(analytics?.upcoming_trips ?? 0);

  const topDest = useMemo(() => analytics?.most_visited_destination || "—", [analytics]);
  const topDestSub = useMemo(() =>
    analytics?.most_visited_destination ? `${analytics.most_visited_count ?? 0} trips` : "No data yet",
    [analytics]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 fade-up">
        <div>
          <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Dashboard</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
            {me?.name ? `Welcome back, ${me.name.split(" ")[0]} 👋` : "Your sessions and account overview"}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/app/trips/new")}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Create Trip
        </button>
      </div>

      {err && (
        <div className="card p-4 border-l-4" style={{ borderLeftColor: "var(--coral)", color: "var(--coral)" }}>
          {err}
        </div>
      )}

      {/* Profile card */}
      <div className="card p-5 fade-up-1">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-base">Profile</h2>
          <button className="btn btn-ghost text-xs py-1.5" onClick={() => navigate("/app/account")}>
            Edit →
          </button>
        </div>
        {loading ? (
          <div className="flex gap-6">
            {[80, 140, 100].map((w, i) => <div key={i} className={`skeleton h-4`} style={{ width: w }} />)}
          </div>
        ) : me ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            {[
              ["Name",   me.name  ?? "—"],
              ["Email",  me.email ?? "—"],
              ["Member since", me.created_at ? new Date(me.created_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : "—"],
            ].map(([label, val]) => (
              <div key={label}>
                <div className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{label}</div>
                <div style={{ color: "var(--text-primary)" }}>{val}</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: "var(--text-muted)" }}>Profile not available.</p>
        )}
      </div>

      {/* Stats grid */}
      <div>
        <div className="flex items-center justify-between mb-3 fade-up-1">
          <h2 className="font-display font-semibold text-base">Travel Insights</h2>
        </div>
        <div className="grid gap-4 grid-cols-2 xl:grid-cols-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : (
            <>
              <StatCard delay="0s" label="Total Trips" accent="var(--teal)"
                icon={<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>}
                value={<span style={{ color: "var(--teal)" }}>{totalTrips}</span>}
                sub="Sessions created" />
              <StatCard delay="0.06s" label="Avg Budget" accent="var(--amber)"
                icon={<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
                value={<span style={{ color: "var(--amber)" }}>₹{avgBudget.toLocaleString()}</span>}
                sub="Per trip estimate" />
              <StatCard delay="0.12s" label="Top Destination" accent="var(--indigo)"
                icon={<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>}
                value={<span style={{ color: "var(--indigo)", fontSize: "1.5rem" }}>{topDest}</span>}
                sub={topDestSub} />
              <StatCard delay="0.18s" label="Upcoming Trips" accent="var(--coral)"
                icon={<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>}
                value={<span style={{ color: "var(--coral)" }}>{upcoming}</span>}
                sub="Start date in future" />
            </>
          )}
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="fade-up-3">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display font-semibold text-base">Recent Sessions</h2>
          <button className="btn btn-ghost text-xs py-1.5" onClick={() => navigate("/app/trips")}>
            View all →
          </button>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="card p-4">
                <div className="flex justify-between">
                  <div className="space-y-2"><div className="skeleton h-4 w-48" /><div className="skeleton h-3 w-32" /></div>
                  <div className="skeleton h-6 w-20 rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="card p-10 text-center">
            <div className="text-4xl mb-3">✈️</div>
            <h3 className="font-display font-semibold text-lg">No trips yet</h3>
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>Click "Create Trip" to plan your first AI-powered journey.</p>
            <button className="btn btn-primary mt-5" onClick={() => navigate("/app/trips/new")}>Start Planning</button>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.slice(0, 8).map((s, i) => (
              <div key={s.search_id}
                className="card p-4 cursor-pointer hover:border-teal transition-all duration-200 fade-up"
                style={{ animationDelay: `${i * 0.04}s`, cursor: "pointer" }}
                onClick={() => navigate(`/app/sessions/${s.search_id}`)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
                        {s.session_title || `${s.from_location} → ${s.to_location}`}
                      </span>
                      {statusBadge(s.agent_status)}
                    </div>
                    <div className="mt-1.5 flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
                      <span>📅 {s.start_date}{s.end_date ? ` → ${s.end_date}` : ""}</span>
                      {s.budget && <span>💰 ₹{s.budget.toLocaleString()}</span>}
                      {s.data_source && <span className="badge badge-gray py-0 px-1.5" style={{ fontSize: 10 }}>{s.data_source}</span>}
                    </div>
                  </div>
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}
                    style={{ color: "var(--text-muted)", flexShrink: 0 }}>
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
