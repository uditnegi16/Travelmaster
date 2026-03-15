import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../../lib/api";

type Role = "user" | "assistant";
type RankedResponse = {
  narrative?: string;
  recommended_flights?: any[];
  other_flights?: any[];
  recommended_hotels?: any[];
  other_hotels?: any[];
  places?: any[];
  weather?: any[];
  budget?: any;
};
type ChatMessage = {
  id?: string;
  role: Role;
  content: string;
  created_at?: string;
  ranked?: RankedResponse | null;
};
type CreatedSession = { search_id: string };

const EXAMPLES = [
  "Plan a 3 day trip from Delhi to Mumbai, 2 adults, budget ₹30k, March 25–27",
  "Weekend trip to Manali from Mumbai, solo traveler, under ₹15k",
  "Jaipur + Agra from Bangalore, 5 days, family of 4, ₹80k budget",
];

/* ─── Flight row ─── */
function FlightRow({ f, rec }: { f: any; rec?: boolean }) {
  const airline = f.airline || f.carrier || "Flight";
  const dep = (f.departure_time || "").replace("T", " ").slice(0, 16);
  const arr = (f.arrival_time || "").replace("T", " ").slice(0, 16);
  const price = f.price || f.total_price || "";
  const stops = f.stops ?? f.numberOfStops ?? "—";
  const duration = f.duration || "";
  const cabin = f.cabin_class || "";
  const url = f.booking_url || "";
  return (
    <tr className="border-b" style={{ borderColor: "var(--border)" }}>
      <td className="py-2 px-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
        {rec && <span className="mr-1">⭐</span>}{airline}
      </td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{dep}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{arr}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{duration}</td>
      <td className="py-2 px-3 text-xs text-center" style={{ color: "var(--text-muted)" }}>{stops}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{cabin}</td>
      <td className="py-2 px-3 text-xs font-bold" style={{ color: "var(--teal)" }}>
        {typeof price === "number" ? `₹${price.toLocaleString()}` : price}
      </td>
      <td className="py-2 px-3">
        {url ? (
          <a href={url} target="_blank" rel="noopener noreferrer"
            className="text-[10px] px-2 py-0.5 rounded-full font-semibold whitespace-nowrap"
            style={{ background: "var(--teal)", color: "#000" }}>
            Book →
          </a>
        ) : <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>—</span>}
      </td>
    </tr>
  );
}

/* ─── Hotel row ─── */
function HotelRow({ h, rec }: { h: any; rec?: boolean }) {
  const name = h.name || h.hotel_name || "Hotel";
  const stars = h.stars || h.star_category || 0;
  const rating = h.rating || "";
  const price = h.price_per_night || h.price || "";
  const city = h.city || "";
  const checkIn = h.check_in || "";
  const checkOut = h.check_out || "";
  const url = h.booking_url || "";
  return (
    <tr className="border-b" style={{ borderColor: "var(--border)" }}>
      <td className="py-2 px-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
        {rec && <span className="mr-1">⭐</span>}{name}
      </td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{city}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--amber)" }}>
        {stars > 0 ? "★".repeat(Math.min(5, Math.round(Number(stars)))) : "—"}
      </td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{rating || "—"}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{checkIn}</td>
      <td className="py-2 px-3 text-xs" style={{ color: "var(--text-muted)" }}>{checkOut}</td>
      <td className="py-2 px-3 text-xs font-bold" style={{ color: "var(--amber)" }}>
        {typeof price === "number" ? `₹${price.toLocaleString()}/n` : price}
      </td>
      <td className="py-2 px-3">
        {url ? (
          <a href={url} target="_blank" rel="noopener noreferrer"
            className="text-[10px] px-2 py-0.5 rounded-full font-semibold whitespace-nowrap"
            style={{ background: "var(--amber)", color: "#000" }}>
            Book →
          </a>
        ) : <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>—</span>}
      </td>
    </tr>
  );
}

/* ─── Inline results widget ─── */
function InlineResults({ ranked }: { ranked: RankedResponse }) {
  const [tab, setTab] = useState<"flights" | "hotels" | "places" | "weather" | "budget">("flights");

  const recFlights = ranked.recommended_flights ?? [];
  const otherFlights = ranked.other_flights ?? [];
  const recHotels = ranked.recommended_hotels ?? [];
  const otherHotels = ranked.other_hotels ?? [];
  const places = ranked.places ?? [];
  const weather = ranked.weather ?? [];
  const allFlights = [...recFlights, ...otherFlights];
  const allHotels = [...recHotels, ...otherHotels];

  const tabs = [
    { key: "flights", label: `✈️ Flights (${allFlights.length})` },
    { key: "hotels", label: `🏨 Hotels (${allHotels.length})` },
    { key: "places", label: `📍 Places (${places.length})` },
    { key: "weather", label: `🌤 Weather (${weather.length})` },
    { key: "budget", label: "💰 Budget" },
  ] as const;

  return (
    <div className="mt-3 rounded-xl overflow-hidden border" style={{ borderColor: "var(--border)", background: "var(--bg-elevated)" }}>
      {/* Tab bar */}
      <div className="flex overflow-x-auto border-b" style={{ borderColor: "var(--border)" }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className="px-3 py-2 text-[11px] font-semibold whitespace-nowrap flex-shrink-0 transition-colors"
            style={{
              color: tab === t.key ? "var(--teal)" : "var(--text-muted)",
              borderBottom: tab === t.key ? "2px solid var(--teal)" : "2px solid transparent",
              background: "transparent",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto w-full" style={{ maxHeight: 320, WebkitOverflowScrolling: "touch" }}>
        {/* ── Flights tab ── */}
        {tab === "flights" && (
          allFlights.length === 0
            ? <div className="p-4 text-xs" style={{ color: "var(--text-muted)" }}>No flights found. Amadeus sandbox may be temporarily unavailable.</div>
            : <table className="w-full text-left" style={{ minWidth: 640 }}>
                <thead>
                  <tr style={{ background: "var(--bg-card)" }}>
                    {["Airline", "Departure", "Arrival", "Duration", "Stops", "Cabin", "Price", ""].map(h => (
                      <th key={h} className="py-2 px-3 text-[10px] uppercase tracking-widest font-semibold"
                        style={{ color: "var(--text-muted)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recFlights.length > 0 && (
                    <tr style={{ background: "var(--bg-card)" }}>
                      <td colSpan={8} className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest"
                        style={{ color: "var(--teal)" }}>⭐ Recommended</td>
                    </tr>
                  )}
                  {recFlights.map((f, i) => <FlightRow key={`rec-${i}`} f={f} rec />)}
                  {otherFlights.length > 0 && (
                    <tr style={{ background: "var(--bg-card)" }}>
                      <td colSpan={8} className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest"
                        style={{ color: "var(--text-muted)" }}>Other Options</td>
                    </tr>
                  )}
                  {otherFlights.map((f, i) => <FlightRow key={`other-${i}`} f={f} />)}
                </tbody>
              </table>
        )}

        {/* ── Hotels tab ── */}
        {tab === "hotels" && (
          allHotels.length === 0
            ? <div className="p-4 text-xs" style={{ color: "var(--text-muted)" }}>No hotels found. Amadeus sandbox has limited hotel data for some cities.</div>
            : <table className="w-full text-left" style={{ minWidth: 680 }}>
                <thead>
                  <tr style={{ background: "var(--bg-card)" }}>
                    {["Hotel", "City", "Stars", "Rating", "Check-in", "Check-out", "Price/night", ""].map(h => (
                      <th key={h} className="py-2 px-3 text-[10px] uppercase tracking-widest font-semibold"
                        style={{ color: "var(--text-muted)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recHotels.length > 0 && (
                    <tr style={{ background: "var(--bg-card)" }}>
                      <td colSpan={8} className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest"
                        style={{ color: "var(--amber)" }}>⭐ Recommended</td>
                    </tr>
                  )}
                  {recHotels.map((h, i) => <HotelRow key={`rec-${i}`} h={h} rec />)}
                  {otherHotels.length > 0 && (
                    <tr style={{ background: "var(--bg-card)" }}>
                      <td colSpan={8} className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest"
                        style={{ color: "var(--text-muted)" }}>Other Options</td>
                    </tr>
                  )}
                  {otherHotels.map((h, i) => <HotelRow key={`other-${i}`} h={h} />)}
                </tbody>
              </table>
        )}

        {/* ── Places tab ── */}
        {tab === "places" && (
          places.length === 0
            ? <div className="p-4 text-xs" style={{ color: "var(--text-muted)" }}>No places found.</div>
            : <div className="grid grid-cols-2 gap-2 p-3">
                {places.map((p, i) => (
                  <div key={i} className="card p-3 rounded-xl">
                    <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{p.name}</div>
                    <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>{p.category}</div>
                    {p.rating > 0 && <div className="text-[10px] mt-0.5" style={{ color: "var(--amber)" }}>★ {p.rating}</div>}
                    {p.entry_fee !== undefined && (
                      <div className="text-[10px] mt-0.5" style={{ color: "var(--teal)" }}>
                        {p.entry_fee === 0 ? "Free entry" : `₹${p.entry_fee}`}
                      </div>
                    )}
                  </div>
                ))}
              </div>
        )}

        {/* ── Weather tab ── */}
        {tab === "weather" && (
          weather.length === 0
            ? <div className="p-4 text-xs" style={{ color: "var(--text-muted)" }}>No weather data found.</div>
            : <div className="grid grid-cols-3 gap-2 p-3">
                {weather.map((w, i) => (
                  <div key={i} className="card p-3 rounded-xl text-center">
                    <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{w.date}</div>
                    <div className="text-lg mt-1">{w.condition === "Clear" ? "☀️" : w.condition === "Rain" ? "🌧️" : "⛅"}</div>
                    <div className="text-[10px] mt-1" style={{ color: "var(--text-muted)" }}>{w.condition}</div>
                    <div className="text-xs font-bold mt-1" style={{ color: "var(--teal)" }}>{w.temp_max_c}°C</div>
                    <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{w.temp_min_c}°C min</div>
                    {w.rain_chance > 0 && <div className="text-[10px]" style={{ color: "var(--indigo)" }}>💧 {w.rain_chance}%</div>}
                  </div>
                ))}
              </div>
        )}

        {/* ── Budget tab ── */}
        {tab === "budget" && ranked.budget && (
          <div className="p-4 space-y-3">
            {ranked.budget.enrichment?.verdict && (
              <div className="px-3 py-2 rounded-lg text-xs font-semibold"
                style={{
                  background: ranked.budget.enrichment.verdict.status === "approved" ? "rgba(74,222,128,0.1)" : "rgba(240,96,96,0.1)",
                  color: ranked.budget.enrichment.verdict.status === "approved" ? "var(--mint)" : "var(--coral)",
                }}>
                {ranked.budget.enrichment.verdict.status === "approved" ? "✅" : "⚠️"} {ranked.budget.enrichment.verdict.message}
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              {ranked.budget.enrichment?.cost_breakdown && Object.entries(ranked.budget.enrichment.cost_breakdown).map(([k, v]) => (
                <div key={k} className="card-elevated p-2 rounded-lg flex justify-between items-center">
                  <span className="text-[10px] capitalize" style={{ color: "var(--text-muted)" }}>{k}</span>
                  <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>₹{Number(v).toLocaleString()}</span>
                </div>
              ))}
            </div>
            {ranked.budget.total_cost && (
              <div className="card-elevated p-3 rounded-lg flex justify-between items-center">
                <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>Total</span>
                <span className="text-sm font-bold" style={{ color: "var(--teal)" }}>₹{Number(ranked.budget.total_cost).toLocaleString()}</span>
              </div>
            )}
            {ranked.budget.enrichment?.health_score && (
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                Health score: <span style={{ color: "var(--teal)" }}>{ranked.budget.enrichment.health_score.score}/10</span>
                {" · "}{ranked.budget.enrichment.health_score.severity}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
function NarrativeBlock({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = content.length > 600;
  const preview = isLong && !expanded ? content.slice(0, 600) + "…" : content;
  return (
    <div>
      <div className="text-sm whitespace-pre-wrap" style={{ color: "var(--text-primary)", lineHeight: 1.7 }}>
        {preview}
      </div>
      {isLong && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="mt-2 text-xs font-semibold px-3 py-1 rounded-full transition-colors"
          style={{ background: "var(--teal)", color: "#000" }}
        >
          {expanded ? "▲ Show less" : "▼ Read full plan"}
        </button>
      )}
    </div>
  );
}
/* ─── Main page ─── */
export default function TripNew() {
  const { getToken, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const { id: urlSessionId } = useParams<{ id?: string }>();
  const [sessionId, setSessionId] = useState<string | null>(urlSessionId ?? null);
  const [loadingHistory, setLoadingHistory] = useState(!!urlSessionId);  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [step, setStep] = useState<"idle" | "creating" | "running" | "ranking" | "done">("idle");
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const canSend = useMemo(() => !!draft.trim() && !busy, [draft, busy]);

    // Load existing session messages + ranked on mount (when opened from sessions/:id)
    useEffect(() => {
      if (!urlSessionId) return;
      (async () => {
        setLoadingHistory(true);
        try {
          const token = await getToken();
          if (!token) return;
          const [msgs, rankedRes] = await Promise.all([
            apiGet<any[]>(`/me/sessions/${urlSessionId}/messages`, token),
            apiGet<RankedResponse>(`/me/sessions/${urlSessionId}/ranked`, token).catch(() => null),
          ]);
          const loaded = (msgs || [])
            .filter((m: any) => {
              if (m.role === "system") return false;
              const t = m.content?.trim() ?? "";
              if (t.startsWith("{") || t.startsWith("[")) return false;
              return true;
            })
            .map((m: any, idx: number, arr: any[]) => {
              const isLastAssistant = m.role === "assistant" &&
                arr.slice(idx + 1).every((x: any) => x.role !== "assistant");
              return isLastAssistant && rankedRes
                ? { ...m, id: m.message_id, ranked: rankedRes }
                : { ...m, id: m.message_id };
            });
          setMessages(loaded);
          setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
        } catch (e) {
          console.error("Failed to load session history", e);
        } finally {
          setLoadingHistory(false);
        }
      })();
    }, [urlSessionId]);

  const scrollToBottom = () => setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);

  const send = async (text?: string) => {
    const content = (text ?? draft).trim();
    if (!content || busy) return;
    setBusy(true); setErr(""); setDraft("");

    const userMsg: ChatMessage = { role: "user", content, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    scrollToBottom();

    try {
      if (!isSignedIn) throw new Error("You must be signed in.");
      const token = await getToken();
      if (!token) throw new Error("Missing Clerk token");

      let sid = sessionId;
      if (!sid) {
        setStep("creating");
        const created = await apiPost<CreatedSession>("/me/sessions/from-chat", { user_query: content }, token);
        sid = created.search_id;
        setSessionId(sid);
      }

      await apiPost(`/me/sessions/${sid}/messages`, { role: "user", content, metadata: { source: "trip_new" } }, token);

      setStep("running");
      await apiPost(`/me/sessions/${sid}/run`, {}, (await getToken())!);

      setStep("ranking");
      await apiPost(`/me/sessions/${sid}/rank`, {}, (await getToken())!);

      const rankedRes = await apiGet<RankedResponse>(`/me/sessions/${sid}/ranked`, (await getToken())!);
      setStep("done");

      const assistantText = rankedRes?.narrative?.trim() || "Trip computed — see results below.";

      // Attach ranked data to the assistant message so it renders inline
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: assistantText,
        created_at: new Date().toISOString(),
        ranked: rankedRes,
      };
      setMessages(prev => [...prev, assistantMsg]);
      scrollToBottom();

      await apiPost(`/me/sessions/${sid}/messages`,
        { role: "assistant", content: assistantText, metadata: { source: "ranked_output" } },
        (await getToken())!
      );

    } catch (e: any) {
      setErr(e?.message || "Failed to send message");
      setStep("idle");
    } finally {
      setBusy(false);
    }
  };

  const stepLabel = {
    idle: "", creating: "Creating session…", running: "🤖 Running AI agent…", ranking: "📊 Ranking results…", done: ""
  }[step];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 fade-up">
        <div>
          <h1 className="font-display text-2xl font-bold" style={{ color: "var(--text-primary)" }}>New Trip</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>Describe your trip — AI finds flights, hotels & places</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button className="btn text-xs py-2" onClick={() => navigate("/app/trips")}>← Back</button>
          {sessionId && (
            <>
              {/* PDF Export */}
              <button
                className="btn text-xs py-2"
                disabled={pdfLoading}
                onClick={async () => {
                  setPdfLoading(true);
                  try {
                    const token = await getToken();
                    const res = await fetch(`http://127.0.0.1:8000/me/sessions/${sessionId}/pdf`, {
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      alert(err.detail || "PDF export not available yet.");
                      return;
                    }
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url; a.download = `trip_${sessionId}.pdf`; a.click();
                    URL.revokeObjectURL(url);
                  } catch { alert("Failed to export PDF."); }
                  finally { setPdfLoading(false); }
                }}
              >
                {pdfLoading ? "Exporting…" : "⬇ PDF"}
              </button>

              {/* Share */}
              <button
                className="btn text-xs py-2"
                disabled={shareLoading}
                onClick={async () => {
                  setShareLoading(true);
                  try {
                    const token = await getToken();
                    const res = await fetch(`http://127.0.0.1:8000/me/sessions/${sessionId}/share`, {
                      method: "POST",
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      alert(err.detail || "Trip sharing not available yet.");
                      return;
                    }
                    const data = await res.json();
                    setShareToken(data.share_token);
                    const link = `${window.location.origin}/share/${data.share_token}`;
                    await navigator.clipboard.writeText(link).catch(() => {});
                    alert(`Share link copied!\n\n${link}`);
                  } catch { alert("Failed to create share link."); }
                  finally { setShareLoading(false); }
                }}
              >
                {shareLoading ? "Sharing…" : shareToken ? "🔗 Shared" : "🔗 Share"}
              </button>

              <button className="btn btn-primary text-xs py-2" onClick={() => navigate(`/app/sessions/${sessionId}`)}>
                Open Session →
              </button>
            </>
          )}
        </div>
      </div>

      {err && <div className="card p-3" style={{ borderLeft: "3px solid var(--coral)", color: "var(--coral)", fontSize: 14 }}>{err}</div>}

      {/* Full width chat — no right panel anymore */}
      <div className="card overflow-hidden flex flex-col fade-up-1" style={{ height: 800 }}>
        {/* Chat header */}
        <div className="flex items-center justify-between px-5 py-3 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">Chat</span>
            {sessionId && <span className="badge badge-teal text-[10px] py-0">Session active</span>}
          </div>
          {stepLabel && <span className="text-xs badge badge-amber animate-pulse">{stepLabel}</span>}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
          {loadingHistory ? (
            <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Loading conversation…
            </div>
          ) : messages.length === 0 ? (
            <div className="space-y-5 max-w-xl">
              <div className="text-sm" style={{ color: "var(--text-muted)" }}>
                Describe your trip and the AI agent will find flights, hotels, and places for you.
              </div>
              <div>
                <div className="text-xs uppercase tracking-widest mb-3 font-semibold" style={{ color: "var(--text-muted)" }}>Quick examples</div>
                <div className="space-y-2">
                  {EXAMPLES.map(ex => (
                    <button key={ex}
                      className="w-full text-left card-elevated p-3 rounded-xl text-sm hover:border-teal-500 transition-colors"
                      style={{ color: "var(--text-secondary)" }}
                      onClick={() => send(ex)}>
                      "{ex}"
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.filter(m => {
              const t = m.content?.trim() ?? "";
              if (t.startsWith("{") || t.startsWith("[")) return false;
              return true;
            }).map((m, idx) => (
              <div key={m.id ?? `${m.role}-${idx}`}
                  className={m.role === "user" ? "ml-auto max-w-[85%] min-w-0" : "mr-auto w-full max-w-full min-w-0"}>
                  <div className="text-[10px] uppercase tracking-widest mb-1.5 px-1" style={{ color: "var(--text-muted)" }}>
                  {m.role === "user" ? "You" : "TravelGuru AI"}
                </div>
                <div className={m.role === "user" ? "bubble-user" : "bubble-assistant"}>
                  <NarrativeBlock content={m.content} />
                  {m.ranked && <InlineResults ranked={m.ranked} />}
                </div>
              </div>
            ))
          )}
          {/* Typing indicator */}
          {busy && (
            <div className="mr-auto max-w-xs">
              <div className="text-[10px] uppercase tracking-widest mb-1.5 px-1" style={{ color: "var(--text-muted)" }}>TravelGuru AI</div>
              <div className="bubble-assistant">
                <div className="flex gap-1 items-center py-1">
                  {[0, 1, 2].map(i => (
                    <span key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                      style={{ background: "var(--teal)", animationDelay: `${i * 0.15}s` }} />
                  ))}
                  {stepLabel && <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>{stepLabel}</span>}
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Composer */}
        <div className="border-t p-4" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
          <div className="flex gap-3 items-end">
            <textarea
              className="input flex-1 min-h-[48px] max-h-[140px]"
              placeholder="e.g. Plan a 5-day Goa trip from Delhi under ₹40k for 2 people…"
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); } }}
              disabled={busy}
            />
            <button className="btn btn-primary px-5" style={{ height: 48 }} disabled={!canSend} onClick={() => void send()}>
              {busy ? (
                <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
              ) : "Send"}
            </button>
          </div>
          <div className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>Enter to send • Shift+Enter for newline</div>
        </div>
      </div>
    </div>
  );
}