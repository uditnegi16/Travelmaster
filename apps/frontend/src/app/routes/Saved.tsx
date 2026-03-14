import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet, apiDelete } from "../../lib/api";
import { useNavigate } from "react-router-dom";

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
  created_at?: string | null;
};

function statusBadge(status?: string | null) {
  if (!status) return null;
  const s = status.toLowerCase();
  if (s.includes("done") || s.includes("complete") || s.includes("success"))
    return <span className="badge badge-mint">{status}</span>;
  if (s.includes("running") || s.includes("pending"))
    return <span className="badge badge-amber">{status}</span>;
  return <span className="badge badge-gray">{status}</span>;
}

export default function Saved() {
  const { getToken, isSignedIn } = useAuth();
  const [items, setItems] = useState<SearchSession[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setErr("");
        if (!isSignedIn) return;
        const token = await getToken();
        if (!token) throw new Error("Missing Clerk token");
        const data = await apiGet<SearchSession[]>("/me/saved-sessions", token);
        setItems(data || []);
      } catch (e: any) {
        setErr(e?.message || "Failed to load saved items");
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken, isSignedIn]);

  const handleUnsave = async (e: React.MouseEvent, searchId: string) => {
    e.stopPropagation();
    setRemovingId(searchId);
    try {
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");
      await apiDelete(`/me/sessions/${searchId}/save`, token);
      setItems(prev => prev.filter(x => x.search_id !== searchId));
    } catch (e: any) {
      setErr(e?.message || "Failed to unsave");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="fade-up">
        <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Saved Trips</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          {items.length > 0 ? `${items.length} saved trip${items.length !== 1 ? "s" : ""}` : "Trips you bookmark will appear here"}
        </p>
      </div>

      {err && <div className="card p-3" style={{ borderLeft: "3px solid var(--coral)", color: "var(--coral)", fontSize: 14 }}>{err}</div>}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="card p-4">
              <div className="flex justify-between">
                <div className="space-y-2"><div className="skeleton h-4 w-48" /><div className="skeleton h-3 w-32" /></div>
                <div className="skeleton h-8 w-20 rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="card p-10 text-center fade-up">
          <div className="text-5xl mb-3">🔖</div>
          <h3 className="font-display font-semibold text-lg">No saved trips yet</h3>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            Open any trip session and click "Save Trip" to bookmark it here.
          </p>
          <button className="btn btn-primary mt-5" onClick={() => navigate("/app/trips")}>Browse Trips</button>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((s, i) => (
            <div key={s.search_id}
              className="card p-4 cursor-pointer transition-all duration-200 fade-up"
              style={{ animationDelay: `${i * 0.04}s` }}
              onClick={() => navigate(`/app/sessions/${s.search_id}`)}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="flex items-center justify-center w-7 h-7 rounded-lg text-sm"
                      style={{ background: "rgba(245,166,35,0.12)", color: "var(--amber)" }}>🔖</span>
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
                    {s.created_at && <span>Saved {new Date(s.created_at).toLocaleDateString()}</span>}
                    {s.data_source && <span className="badge badge-gray py-0 px-1.5" style={{ fontSize: 10 }}>{s.data_source}</span>}
                  </div>
                </div>

                <button
                  className="btn btn-ghost text-xs py-1.5 px-3 shrink-0"
                  style={{ color: "var(--coral)", border: "1px solid rgba(240,96,96,0.25)" }}
                  disabled={removingId === s.search_id}
                  onClick={e => handleUnsave(e, s.search_id)}>
                  {removingId === s.search_id ? "…" : "Unsave"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
