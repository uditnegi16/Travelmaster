import { useEffect, useState } from "react";
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

export default function Dashboard() {
  const { getToken, isSignedIn } = useAuth();
  const [me, setMe] = useState<UserProfile | null>(null);
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [err, setErr] = useState<string>("");
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setErr("");
        if (!isSignedIn) return;

        const token = await getToken();
        if (!token) throw new Error("Missing Clerk token");

        const profile = await apiGet<UserProfile>("/me", token);
        setMe(profile);

        const sess = await apiGet<SearchSession[]>("/me/sessions", token);
        setSessions(sess);
      } catch (e: any) {
        setErr(e?.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken, isSignedIn]);


    return (
    <div className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="mt-2 text-white/60">Your sessions and account overview.</p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => navigate("/app/trips/new")}
        >
          Create Trip
        </button>
      </div>

      {err ? <p className="mt-4 text-red-400">{err}</p> : null}

      {/* Profile */}
      
      <section className="mt-6">
        <h2 className="text-lg font-semibold">Profile</h2>

        {loading ? (
          <div className="card p-6 mt-3">
            <p className="text-white/70">Loading profile…</p>
          </div>
        ) : me ? (
          <div className="card p-6 mt-3">
            <div className="grid gap-2 text-slate-300">
              <div><span className="text-slate-400">Name:</span> {me.name ?? "—"}</div>
              <div><span className="text-slate-400">Email:</span> {me.email ?? "—"}</div>
              <div>
                <span className="text-slate-400">Member since:</span>{" "}
                {me.created_at ? new Date(me.created_at).toLocaleDateString() : "—"}
              </div>
            </div>
          </div>
        ) : (
          <div className="card p-6 mt-3">
            <p className="text-white/70">Profile not available.</p>
          </div>
        )}
      </section>


      {/* Sessions */}
      <section className="mt-6">
        <h2 className="text-lg font-semibold">Recent Sessions</h2>

        {loading ? (
          <div className="card p-6 mt-3">
            <p className="text-white/70">Loading sessions…</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="card p-8 mt-3 text-center">
            <h3 className="text-lg font-semibold">No trips yet</h3>
            <p className="mt-2 text-white/60">
              Click “Create Trip” to start your first session.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 mt-3">
            {sessions.slice(0, 10).map((s) => (
              <div
              key={s.search_id}
              onClick={() => navigate(`/app/sessions/${s.search_id}`)}
              className="cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-4 hover:bg-white/10 transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-semibold">
                    {s.session_title || `${s.from_location} → ${s.to_location}`}
                  </div>
                  <div className="mt-1 text-sm text-white/70">
                    {s.start_date} {s.end_date ? `to ${s.end_date}` : ""}
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
      </section>

    </div>
  );

}
