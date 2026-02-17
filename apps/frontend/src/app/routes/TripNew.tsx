import { useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import { apiPost } from "../../lib/api"; // adjust path if your api.ts is elsewhere

type CreateSessionPayload = {
  from_location: string;
  to_location: string;
  start_date: string;
  end_date: string;
  num_adults: number;
  num_children: number;
  budget?: number | null;
  trip_type?: string;
  session_title?: string;
};

type Session = {
  search_id: string;
};

export default function TripNew() {
  const { getToken } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState<CreateSessionPayload>({
    from_location: "",
    to_location: "",
    start_date: "",
    end_date: "",
    num_adults: 1,
    num_children: 0,
    budget: null,
    trip_type: "leisure",
    session_title: "",
  });

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const onChange = (k: keyof CreateSessionPayload, v: any) => {
    setForm((p) => ({ ...p, [k]: v }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");

      // Minimal validation
      if (!form.from_location.trim() || !form.to_location.trim()) {
        throw new Error("From and To locations are required.");
      }
      if (!form.start_date || !form.end_date) {
        throw new Error("Start date and end date are required.");
      }

      const payload: CreateSessionPayload = {
        ...form,
        budget: form.budget === null || Number.isNaN(Number(form.budget)) ? null : Number(form.budget),
        num_adults: Number(form.num_adults) || 1,
        num_children: Number(form.num_children) || 0,
        session_title: form.session_title?.trim() ? form.session_title.trim() : undefined,
      };

      const created = await apiPost<Session>("/me/sessions", payload, token);

      navigate(`/app/sessions/${created.search_id}`);
    } catch (e: any) {
      setErr(e?.message || "Failed to create trip");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Create Trip</h1>
          <p className="mt-2 text-white/60">
            Phase-1 DB mode: this creates a session only. AI planning comes later.
          </p>
        </div>

        <button
          className="btn"
          type="button"
          onClick={() => navigate("/app/dashboard")}
        >
          Back
        </button>
      </div>

      {err ? <p className="mt-4 text-red-400">{err}</p> : null}

      <form onSubmit={onSubmit} className="mt-6 max-w-2xl space-y-4">
        <div className="card p-6 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm text-white/70">From</label>
              <input
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.from_location}
                onChange={(e) => onChange("from_location", e.target.value)}
                placeholder="Delhi"
              />
            </div>

            <div>
              <label className="text-sm text-white/70">To</label>
              <input
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.to_location}
                onChange={(e) => onChange("to_location", e.target.value)}
                placeholder="Goa"
              />
            </div>

            <div>
              <label className="text-sm text-white/70">Start Date</label>
              <input
                type="date"
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.start_date}
                onChange={(e) => onChange("start_date", e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm text-white/70">End Date</label>
              <input
                type="date"
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.end_date}
                onChange={(e) => onChange("end_date", e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm text-white/70">Adults</label>
              <input
                type="number"
                min={1}
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.num_adults}
                onChange={(e) => onChange("num_adults", e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm text-white/70">Children</label>
              <input
                type="number"
                min={0}
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.num_children}
                onChange={(e) => onChange("num_children", e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm text-white/70">Budget (optional)</label>
              <input
                type="number"
                min={0}
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.budget ?? ""}
                onChange={(e) => onChange("budget", e.target.value)}
                placeholder="45000"
              />
            </div>

            <div>
              <label className="text-sm text-white/70">Trip Type</label>
              <select
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
                value={form.trip_type}
                onChange={(e) => onChange("trip_type", e.target.value)}
              >
                <option value="leisure">Leisure</option>
                <option value="business">Business</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm text-white/70">Session Title (optional)</label>
            <input
              className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 outline-none focus:border-white/25"
              value={form.session_title ?? ""}
              onChange={(e) => onChange("session_title", e.target.value)}
              placeholder="Goa beach trip"
            />
          </div>

          <div className="flex gap-3">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Trip"}
            </button>

            <button
              className="btn"
              type="button"
              onClick={() => navigate("/app/dashboard")}
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
