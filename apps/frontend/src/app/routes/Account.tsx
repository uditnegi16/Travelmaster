import { useEffect, useState } from "react";
import { useAuth, UserButton } from "@clerk/clerk-react";
import { apiGet } from "../../lib/api";

type UserProfile = {
  account_id: string;
  clerk_user_id: string;
  name?: string | null;
  email?: string | null;
  address?: string | null;
  company?: string | null;
  age?: number | null;
  gender?: string | null;
  created_at?: string;
};

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-3 border-b" style={{ borderColor: "var(--border)" }}>
      <span className="text-sm" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-sm font-medium text-right" style={{ color: "var(--text-primary)", maxWidth: "60%" }}>{value || "—"}</span>
    </div>
  );
}

export default function Account() {
  const { getToken, isSignedIn } = useAuth();
  const [me, setMe] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        if (!isSignedIn) return;
        const token = await getToken();
        if (!token) return;
        const profile = await apiGet<UserProfile>("/me", token);
        setMe(profile);
      } catch (e: any) {
        setErr(e?.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken, isSignedIn]);

  return (
    <div className="space-y-5 max-w-2xl">
      {/* Header */}
      <div className="fade-up">
        <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Account</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>Your profile and preferences</p>
      </div>

      {err && <div className="card p-3" style={{ borderLeft: "3px solid var(--coral)", color: "var(--coral)", fontSize: 14 }}>{err}</div>}

      {/* Avatar + name card */}
      <div className="card p-6 fade-up-1">
        <div className="flex items-center gap-4">
          <div className="relative">
            <UserButton />
          </div>
          <div>
            {loading ? (
              <>
                <div className="skeleton h-5 w-36 mb-2" />
                <div className="skeleton h-4 w-48" />
              </>
            ) : (
              <>
                <div className="font-display font-bold text-lg" style={{ color: "var(--text-primary)" }}>{me?.name || "—"}</div>
                <div className="text-sm mt-0.5" style={{ color: "var(--text-muted)" }}>{me?.email || "—"}</div>
                {me?.created_at && (
                  <div className="mt-2">
                    <span className="badge badge-teal text-[10px]">
                      Member since {new Date(me.created_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Profile details */}
      <div className="card p-5 fade-up-2">
        <h2 className="font-display font-semibold text-sm mb-1" style={{ color: "var(--text-primary)" }}>Profile Details</h2>
        <p className="text-xs mb-4" style={{ color: "var(--text-muted)" }}>Manage your account information via Clerk settings</p>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="flex justify-between py-3 border-b" style={{ borderColor: "var(--border)" }}>
                <div className="skeleton h-4 w-20" />
                <div className="skeleton h-4 w-32" />
              </div>
            ))}
          </div>
        ) : (
          <div>
            <FieldRow label="Full Name"    value={me?.name} />
            <FieldRow label="Email"        value={me?.email} />
            <FieldRow label="Company"      value={me?.company} />
            <FieldRow label="Address"      value={me?.address} />
            <FieldRow label="Age"          value={me?.age ? String(me.age) : null} />
            <FieldRow label="Gender"       value={me?.gender} />
            <div className="flex items-start justify-between py-3">
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>Account ID</span>
              <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{me?.account_id?.slice(0, 16)}…</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
