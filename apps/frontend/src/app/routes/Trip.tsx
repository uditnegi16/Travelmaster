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

export default function Trips() {
  const { getToken, isSignedIn } = useAuth();
  const navigate = useNavigate();
  
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
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
    })();
  }, [getToken, isSignedIn]);

  return (
    <div className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Trips</h1>
          <p className="mt-2 text-white/60">
            Phase-1 DB mode: create trips + view saved sessions.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => navigate("/app/trips/new")}
        >
          + New Trip
        </button>
      </div>

      {err ? <p className="mt-4 text-red-400">{err}</p> : null}

      <div className="mt-6">
        {loading ? (
          <div className="card p-6">
            <p className="text-white/70">Loading trips…</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-semibold">No trips yet</h3>
            <p className="mt-2 text-white/60">Create your first trip session.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {sessions.map((s) => (
              <div
                key={s.search_id}
                onClick={() => navigate(`/app/sessions/${s.search_id}`)}
                className="cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-4 hover:bg-white/10 transition"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-semibold">
                      {s.session_title || `${s.from_location ?? "—"} → ${s.to_location ?? "—"}`}
                    </div>
                    <div className="mt-1 text-sm text-white/70">
                      {(s.start_date ?? "—")} {s.end_date ? `to ${s.end_date}` : ""}
                      {s.last_activity_at ? (
                        <div className="mt-1 text-xs text-white/50">
                          Last activity: {new Date(s.last_activity_at).toLocaleString()}
                        </div>
                      ) : null}

                    </div>
                  </div>

                  <div className="text-right text-sm text-white/70">
                    <div>{s.agent_status ?? "—"}</div>
                    <div className="mt-1">{s.data_source ?? "—"}</div>
                  </div>
                </div>

                <div className="mt-3 text-sm text-white/70">
                  Budget: {s.budget ?? "—"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
