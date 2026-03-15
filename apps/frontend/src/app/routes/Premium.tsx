// src/app/routes/Premium.tsx
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet } from "../../lib/api";

const CHECK = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const CROWN = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
    <path d="M2 20h20M4 20L2 8l6 4 4-8 4 8 6-4-2 12" />
  </svg>
);

const BOLT = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const FREE_FEATURES = [
  "5 AI trip searches per month",
  "Flights + Hotels + Places",
  "Weather forecast + Budget",
  "Session history",
  "Save trips",
  "PDF export",
  "Shareable trip links",
];

const PREMIUM_FEATURES = [
  "100 AI trip searches per month",
  "Everything in Free",
  "Priority AI agent (faster results)",
  "Advanced trip comparison",
  "Group trip planning",
  "Price alerts on saved trips",
  "Early access to new features",
  "Premium support",
];

type Profile = { tier?: string; searches_this_month?: number; email?: string; name?: string };

export default function Premium() {
  const { getToken } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await apiGet<Profile>("/me", token);
        setProfile(data);
      } catch (e: any) {
        setErr(e?.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const isPremium = profile?.tier === "premium";

  const handleUpgrade = async () => {
    setCheckoutLoading(true);
    setErr("");
    try {
      const token = await getToken();
      const res = await fetch("http://127.0.0.1:8000/me/create-checkout-session", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to start checkout");
      }
      const { url } = await res.json();
      window.location.href = url;
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const freeUsed = profile?.searches_this_month || 0;
  const freeLimit = 5;
  const usagePercent = Math.min((freeUsed / freeLimit) * 100, 100);

  return (
    <div className="max-w-4xl space-y-8">

      {/* Header */}
      <div className="fade-up">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #f59e0b, #ef4444)" }}>
            <CROWN />
          </div>
          <div>
            <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              TravelGuru Premium
            </h1>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Plan more trips, faster — with priority AI
            </p>
          </div>
        </div>
      </div>

      {err && (
        <div className="card p-3" style={{ borderLeft: "3px solid var(--coral)", color: "var(--coral)", fontSize: 14 }}>
          {err}
        </div>
      )}

      {/* Current plan status */}
      {!loading && profile && (
        <div className="card p-5 fade-up-1" style={{
          border: isPremium ? "1px solid rgba(245,158,11,0.4)" : "1px solid var(--border)",
          background: isPremium ? "rgba(245,158,11,0.05)" : undefined
        }}>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-xs uppercase tracking-widest font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
                Current Plan
              </p>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-lg" style={{ color: "var(--text-primary)" }}>
                  {isPremium ? "Premium" : "Free"}
                </span>
                {isPremium && (
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: "rgba(245,158,11,0.15)", color: "#f59e0b" }}>
                    ✦ Active
                  </span>
                )}
              </div>
            </div>
            {!isPremium && (
              <div className="text-right">
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Searches used this month
                </p>
                <p className="font-bold text-sm mt-0.5" style={{ color: usagePercent >= 100 ? "var(--coral)" : "var(--text-primary)" }}>
                  {freeUsed} / {freeLimit}
                </p>
                <div className="w-32 h-1.5 rounded-full mt-1.5 overflow-hidden" style={{ background: "var(--border)" }}>
                  <div className="h-full rounded-full transition-all"
                    style={{
                      width: `${usagePercent}%`,
                      background: usagePercent >= 100 ? "var(--coral)" : "var(--teal)"
                    }} />
                </div>
              </div>
            )}
          </div>
          {isPremium && (
            <p className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>
              You're on Premium — enjoy 100 AI searches per month and all premium features.
            </p>
          )}
        </div>
      )}

      {/* Pricing cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 fade-up-2">

        {/* Free card */}
        <div className="card p-6 space-y-5">
          <div>
            <p className="text-xs uppercase tracking-widest font-semibold mb-2" style={{ color: "var(--text-muted)" }}>Free</p>
            <div className="flex items-end gap-1">
              <span className="font-display text-4xl font-bold" style={{ color: "var(--text-primary)" }}>₹0</span>
              <span className="text-sm mb-1" style={{ color: "var(--text-muted)" }}>/month</span>
            </div>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>No credit card required</p>
          </div>

          <div className="space-y-2.5">
            {FREE_FEATURES.map(f => (
              <div key={f} className="flex items-start gap-2.5">
                <span style={{ color: "var(--teal)", marginTop: 2, flexShrink: 0 }}><CHECK /></span>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{f}</span>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <div className="w-full py-2.5 rounded-xl text-sm font-semibold text-center"
              style={{ background: "var(--bg-card-elevated)", color: "var(--text-muted)", border: "1px solid var(--border)" }}>
              {isPremium ? "Previous Plan" : "Current Plan"}
            </div>
          </div>
        </div>

        {/* Premium card */}
        <div className="card p-6 space-y-5 relative overflow-hidden"
          style={{ border: "1px solid rgba(245,158,11,0.35)" }}>

          {/* Glow */}
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: "radial-gradient(ellipse at top right, rgba(245,158,11,0.08) 0%, transparent 70%)" }} />

          {/* Badge */}
          <div className="absolute top-4 right-4">
            <span className="text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wide"
              style={{ background: "linear-gradient(135deg, #f59e0b, #ef4444)", color: "#000" }}>
              Most Popular
            </span>
          </div>

          <div>
            <p className="text-xs uppercase tracking-widest font-semibold mb-2" style={{ color: "#f59e0b" }}>Premium</p>
            <div className="flex items-end gap-1">
              <span className="font-display text-4xl font-bold" style={{ color: "var(--text-primary)" }}>₹399</span>
              <span className="text-sm mb-1" style={{ color: "var(--text-muted)" }}>/month</span>
            </div>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Cancel anytime</p>
          </div>

          <div className="space-y-2.5">
            {PREMIUM_FEATURES.map(f => (
              <div key={f} className="flex items-start gap-2.5">
                <span style={{ color: "#f59e0b", marginTop: 2, flexShrink: 0 }}><CHECK /></span>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{f}</span>
              </div>
            ))}
          </div>

          <div className="pt-2">
            {isPremium ? (
              <div className="w-full py-2.5 rounded-xl text-sm font-semibold text-center"
                style={{ background: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.3)" }}>
                ✦ You're on Premium
              </div>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={checkoutLoading}
                className="w-full py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all"
                style={{
                  background: checkoutLoading ? "rgba(245,158,11,0.3)" : "linear-gradient(135deg, #f59e0b, #ef4444)",
                  color: checkoutLoading ? "#f59e0b" : "#000",
                  boxShadow: checkoutLoading ? "none" : "0 4px 20px rgba(245,158,11,0.3)"
                }}
              >
                {checkoutLoading ? (
                  <>
                    <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                    </svg>
                    Redirecting to payment…
                  </>
                ) : (
                  <><BOLT /> Upgrade to Premium</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stripe trust note */}
      {!isPremium && (
        <div className="fade-up-3 flex items-center justify-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          Payments secured by Stripe · Cancel anytime · No hidden fees
        </div>
      )}

      {/* FAQ */}
      <div className="card p-6 fade-up-3 space-y-4">
        <h2 className="font-display font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
          Frequently Asked Questions
        </h2>
        {[
          ["What counts as a search?", "Every time you send a trip query to the AI agent — it searches flights, hotels, places and weather all at once. That counts as 1 search."],
          ["When does my limit reset?", "Free tier resets on the 1st of every month. Premium users get 100 searches every month."],
          ["Can I cancel anytime?", "Yes — cancel from your account settings. You keep Premium access until the end of the billing period."],
          ["Is my payment secure?", "All payments are processed by Stripe, the same payment provider used by Amazon, Google and thousands of other companies."],
        ].map(([q, a]) => (
          <div key={q} className="border-b pb-4 last:border-0 last:pb-0" style={{ borderColor: "var(--border)" }}>
            <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>{q}</p>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>{a}</p>
          </div>
        ))}
      </div>
    </div>
  );
}