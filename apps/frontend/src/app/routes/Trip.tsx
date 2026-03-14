import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "../../lib/api";

type SearchSession = {
  search_id: string;
  session_title?: string | null;
  from_location?: string | null;
  to_location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  budget?: number | null;
  agent_status?: string | null;
  data_source?: string | null;
  last_activity_at?: string | null;
  created_at?: string | null;
};

type FilterType = "all" | "done" | "pending";

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

export default function Trips() {
  const { getToken, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      setErr("");
      if (!isSignedIn) return;
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");
      const data = await apiGet<SearchSession[]>("/me/sessions", token);
      setSessions(data || []);
    } catch (e: any) {
      setErr(e?.message || "Failed to load trips");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSessions(); }, [getToken, isSignedIn]);

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map(s => s.search_id)));
    }
  };

  const deleteSelected = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} trip(s)? This cannot be undone.`)) return;
    setDeleting(true);
    const token = await getToken();
    await Promise.all(
      Array.from(selected).map(id =>
        fetch(`http://127.0.0.1:8000/me/sessions/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        })
      )
    );
    setSelected(new Set());
    await fetchSessions();
    setDeleting(false);
  };

  const filtered = sessions.filter((s) => {
    const q = search.toLowerCase();
    const matchSearch = !q ||
      s.session_title?.toLowerCase().includes(q) ||
      s.from_location?.toLowerCase().includes(q) ||
      s.to_location?.toLowerCase().includes(q);
    const status = s.agent_status?.toLowerCase() ?? "";
    const matchFilter =
      filter === "all" ? true :
      filter === "done" ? (status.includes("done") || status.includes("complete") || status.includes("success")) :
      filter === "pending" ? (status.includes("running") || status.includes("pending")) :
      true;
    return matchSearch && matchFilter;
  });

  const FILTERS: { key: FilterType; label: string }[] = [
    { key: "all",     label: `All (${sessions.length})` },
    { key: "done",    label: "Completed" },
    { key: "pending", label: "Pending" },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 fade-up">
        <div>
          <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Trips</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>All your travel sessions</p>
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <button
              className="btn text-xs py-2"
              style={{ background: "rgba(239,68,68,0.1)", color: "#f87171", border: "1px solid rgba(239,68,68,0.2)" }}
              onClick={deleteSelected}
              disabled={deleting}
            >
              {deleting ? "Deleting..." : `Delete (${selected.size})`}
            </button>
          )}
          <button className="btn btn-primary" onClick={() => navigate("/app/trips/new")}>
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Trip
          </button>
        </div>
      </div>

      {err && (
        <div className="card p-4" style={{ borderLeft: "3px solid var(--coral)", color: "var(--coral)" }}>{err}</div>
      )}

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3 fade-up-1">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} style={{ color: "var(--text-muted)" }}>
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="input pl-9" placeholder="Search destinations, titles…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-2">
          {FILTERS.map(f => (
            <button key={f.key}
              className={`btn text-xs py-2 ${filter === f.key ? "btn-primary" : ""}`}
              onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Select all bar — shows only when list is not empty */}
      {!loading && filtered.length > 0 && (
        <div className="flex items-center gap-3 px-1 fade-up-1">
          <input
            type="checkbox"
            checked={selected.size === filtered.length && filtered.length > 0}
            onChange={toggleSelectAll}
            className="w-4 h-4 accent-teal-400 cursor-pointer"
          />
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {selected.size > 0 ? `${selected.size} selected` : "Select all"}
          </span>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card p-4">
              <div className="flex justify-between">
                <div className="space-y-2"><div className="skeleton h-4 w-52" /><div className="skeleton h-3 w-36" /></div>
                <div className="skeleton h-6 w-20 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-10 text-center">
          <div className="text-5xl mb-3">🗺️</div>
          <h3 className="font-display font-semibold text-lg">{sessions.length === 0 ? "No trips yet" : "No results"}</h3>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            {sessions.length === 0 ? "Create your first AI-powered trip." : "Try adjusting your search or filter."}
          </p>
          {sessions.length === 0 && (
            <button className="btn btn-primary mt-5" onClick={() => navigate("/app/trips/new")}>Start Planning</button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((s, i) => (
            <div key={s.search_id}
              className={`card p-4 cursor-pointer transition-all duration-200 fade-up ${selected.has(s.search_id) ? "ring-1 ring-teal-500/40" : ""}`}
              style={{ animationDelay: `${i * 0.04}s` }}
              onClick={() => navigate(`/app/sessions/${s.search_id}`)}>
              <div className="flex items-start gap-3">
                {/* Checkbox */}
                <div className="pt-1" onClick={e => toggleSelect(s.search_id, e)}>
                  <input
                    type="checkbox"
                    checked={selected.has(s.search_id)}
                    onChange={() => {}}
                    className="w-4 h-4 accent-teal-400 cursor-pointer"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="flex items-center justify-center w-7 h-7 rounded-lg text-sm"
                          style={{ background: "rgba(14,196,168,0.12)", color: "var(--teal)" }}>✈</span>
                        <span className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
                          {s.session_title || `${s.from_location ?? "—"} → ${s.to_location ?? "—"}`}
                        </span>
                        {statusBadge(s.agent_status)}
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
                        {(s.start_date || s.end_date) && (
                          <span>📅 {s.start_date ?? "—"}{s.end_date ? ` → ${s.end_date}` : ""}</span>
                        )}
                        {s.budget && <span>💰 ₹{Number(s.budget).toLocaleString()}</span>}
                        {s.data_source && <span className="badge badge-gray py-0 px-1.5" style={{ fontSize: 10 }}>{s.data_source}</span>}
                        {s.last_activity_at && (
                          <span>🕐 {new Date(s.last_activity_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}
                      style={{ color: "var(--text-muted)", flexShrink: 0, marginTop: 4 }}>
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}