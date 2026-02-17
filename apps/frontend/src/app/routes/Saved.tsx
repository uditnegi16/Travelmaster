import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet, apiDelete} from "../../lib/api";
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
  last_activity_at?: string | null;
  created_at?: string | null;
};

export default function Saved() {
  const { getToken, isSignedIn } = useAuth();
  const [items, setItems] = useState<SearchSession[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const handleUnsave = async (searchId: string) => {
    try {
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");

      await apiDelete(`/me/sessions/${searchId}/save`, token);

      // remove from UI instantly
      setItems((prev) => prev.filter((x) => x.search_id !== searchId));
    } catch (e: any) {
      setErr(e?.message || "Failed to unsave");
    }
  };

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


  return (
    <div>
      <h1 className="text-2xl font-bold">Saved Trips</h1>
      <p className="muted mt-2">Trips you’ve saved or shortlisted will appear here.</p>

      {err ? <p className="mt-4 text-red-300">{err}</p> : null}

      <div className="mt-6 grid gap-4">
        <div className="mt-6">
      {loading ? (
        <div className="card p-6">
          <p className="text-white/70">Loading saved trips…</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card p-8 text-center">
          <h3 className="text-lg font-semibold">No saved trips yet</h3>
          <p className="mt-2 text-white/60">
            Saved/shortlisted items will appear here.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {items.map((s) => (
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
                    </div>
                    {s.created_at ? (
                      <div className="mt-1 text-xs text-white/50">
                        Saved: {new Date(s.created_at).toLocaleString()}
                      </div>
                    ) : null}
                  </div>

                  <div className="text-right text-sm text-white/70">
                    <div>{s.agent_status ?? "—"}</div>
                    <div className="mt-1">{s.data_source ?? "—"}</div>

                    <button
                      className="btn mt-3"
                      onClick={(e) => {
                        e.stopPropagation(); // don't open session detail
                        handleUnsave(s.search_id);
                      }}
                    >
                      Unsave
                    </button>
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
    </div>
  );
}
