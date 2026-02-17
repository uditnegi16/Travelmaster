import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { apiGet, apiPost, apiDelete } from "../../lib/api";

type Session = {
  search_id: string;
  from_location: string;
  to_location: string;
  start_date: string;
  end_date?: string | null;
  budget?: number | null;
  agent_status?: string | null;
  data_source?: string | null;
  session_title?: string | null;
};

export default function SessionDetail() {
  const { id } = useParams();
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<Session | null>(null);
  const [err, setErr] = useState("");

  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const toggleSave = async () => {
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");

      if (!saved) {
        await apiPost(`/me/sessions/${id}/save`, {}, token);
        setSaved(true);
      } else {
        await apiDelete(`/me/sessions/${id}/save`, token);
        setSaved(false);
      }
    } catch (e: any) {
      setErr(e?.message || "Failed to update save state");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setErr("");
        const token = await getToken();
        if (!token) throw new Error("Missing token");

        const s = await apiGet<Session>(`/me/sessions/${id}`, token);
        setData(s);
        const savedRes = await apiGet<{ saved: boolean }>(`/me/sessions/${id}/saved`, token);
        setSaved(!!savedRes.saved);
      } catch (e: any) {
        setErr(e?.message || "Failed to load session");
      } finally {
        setLoading(false);
      }
    })();
  }, [id, getToken]);

  return (
    <div className="space-y-4">
      <div className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold">Session Details</h1>
            <p className="muted mt-2">DB-only view (agent output later).</p>
          </div>

          <button
            className={`btn ${saved ? "" : "btn-primary"}`}
            onClick={toggleSave}
            disabled={saving}
          >
            {saved ? "Saved ✓" : "Save Trip"}
          </button>
        </div>
      </div>

      <div className="card p-6">
        {err ? <p className="text-red-300">{err}</p> : null}

        {loading ? (
          <p className="muted">Loading…</p>
        ) : !data ? (
          <p className="muted">Session not available</p>
        ) : (
          <div className="space-y-4">
            <div className="text-lg font-bold">
              {data.from_location} → {data.to_location}
            </div>

            <div className="muted">
              {data.start_date} {data.end_date ? `to ${data.end_date}` : ""}
            </div>

            <div className="muted">
              Budget: {data.budget ?? "—"} | Status: {data.agent_status ?? "—"} | Source:{" "}
              {data.data_source ?? "—"}
            </div>

            <div className="grid gap-4">
              <div className="card p-5">
                <div className="text-sm text-white/60">Session Title</div>
                <div className="mt-1 text-lg font-semibold">
                  {data.session_title ?? "—"}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="card p-5">
                  <div className="text-sm text-white/60">Route</div>
                  <div className="mt-1 font-medium">
                    {(data.from_location ?? "—") + " → " + (data.to_location ?? "—")}
                  </div>
                </div>

                <div className="card p-5">
                  <div className="text-sm text-white/60">Dates</div>
                  <div className="mt-1 font-medium">
                    {(data.start_date ?? "—") + " to " + (data.end_date ?? "—")}
                  </div>
                </div>

                <div className="card p-5">
                  <div className="text-sm text-white/60">Budget</div>
                  <div className="mt-1 font-medium">{data.budget ?? "—"}</div>
                </div>

                <div className="card p-5">
                  <div className="text-sm text-white/60">Status</div>
                  <div className="mt-1 font-medium">
                    {(data.agent_status ?? "—") + " | " + (data.data_source ?? "—")}
                  </div>
                </div>
              </div>

              <div className="card p-5">
                <div className="text-sm text-white/60">Notes</div>
                <div className="mt-2 text-white/80">
                  Agent chat not connected yet. This page shows DB session metadata only.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
