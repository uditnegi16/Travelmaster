// src/app/routes/SharedTrip.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Plane } from "lucide-react";

export default function SharedTrip() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/shared/${token}`)
      .then(r => { if (!r.ok) throw new Error("Trip not found or link revoked."); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Loading shared trip…</p>
    </div>
  );
  if (error) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <p className="text-red-400 text-sm mb-2">{error}</p>
        <a href="/" className="text-blue-400 text-xs hover:underline">Go to TravelGuru →</a>
      </div>
    </div>
  );
  if (!data) return null;

  const sess = data.session || {};
  const flights = data.recommended_flights || [];
  const hotels  = data.recommended_hotels || [];
  const places  = data.places || [];

  return (
    <div className="min-h-screen" style={{ background: "#080c14", color: "#f0f4ff" }}>

      {/* Header — full width, consistent */}
      <div style={{
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        background: "rgba(14,21,32,0.95)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 30,
        width: "100%",
      }}>
        <div style={{
          maxWidth: 720,
          margin: "0 auto",
          padding: "0 16px",
          height: 56,
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}>
          <div style={{
            width: 30, height: 30,
            background: "linear-gradient(135deg, #0ec4a8, #6b7ff5)",
            borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Plane size={14} color="#080c14" />
          </div>
          <span style={{ fontFamily: "Syne, sans-serif", fontWeight: 700, fontSize: 15 }}>
            TravelGuru
          </span>
          <span style={{
            fontSize: 11, color: "rgba(150,175,210,0.5)",
            marginLeft: 4,
            padding: "2px 8px",
            background: "rgba(107,127,245,0.1)",
            borderRadius: 20,
            border: "1px solid rgba(107,127,245,0.2)",
          }}>
            Shared Trip
          </span>
        </div>
      </div>

      {/* Content — same max-width as header */}
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 16px", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* Trip title */}
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, fontFamily: "Syne, sans-serif", margin: 0 }}>
            {sess.from_location || "—"} → {sess.to_location || "—"}
          </h1>
          <p style={{ fontSize: 13, color: "rgba(150,175,210,0.55)", marginTop: 6 }}>
            {sess.start_date} – {sess.end_date} · {sess.num_adults || 1} adult(s)
          </p>
        </div>

        {/* Narrative */}
        {data.narrative && (
          <div style={{
            background: "#0e1520",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 16, padding: 20,
          }}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "#0ec4a8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
              Trip Summary
            </h2>
            <p style={{ fontSize: 14, color: "rgba(200,215,240,0.7)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {data.narrative}
            </p>
          </div>
        )}

        {/* Top Flight */}
        {flights[0] && (
          <div style={{ background: "#0e1520", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: 20 }}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "#0ec4a8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
              Recommended Flight
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                ["Airline", flights[0].airline || flights[0].carrier],
                ["Departure", (flights[0].departure_time || "").slice(0,16).replace("T"," ")],
                ["Arrival",   (flights[0].arrival_time   || "").slice(0,16).replace("T"," ")],
                ["Duration",  flights[0].duration],
                ["Stops",     String(flights[0].stops ?? 0)],
                ["Price",     flights[0].price ? `₹${Number(flights[0].price).toLocaleString()}` : "—"],
              ].map(([label, val]) => (
                <div key={label as string}>
                  <span style={{ fontSize: 11, color: "rgba(150,175,210,0.45)", display: "block", marginBottom: 3 }}>{label}</span>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#f0f4ff", margin: 0 }}>{val || "—"}</p>
                </div>
              ))}
            </div>
            {flights[0].booking_url && (
              <a href={flights[0].booking_url} target="_blank" rel="noopener noreferrer"
                style={{
                  display: "inline-block", marginTop: 16,
                  background: "#0ec4a8", color: "#080c14",
                  fontSize: 12, fontWeight: 700,
                  padding: "8px 16px", borderRadius: 10,
                  textDecoration: "none",
                }}>
                Book Flight →
              </a>
            )}
          </div>
        )}

        {/* Top Hotel */}
        {hotels[0] && (
          <div style={{ background: "#0e1520", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: 20 }}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "#6b7ff5", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
              Recommended Hotel
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                ["Name",        hotels[0].name || hotels[0].hotel_name],
                ["City",        hotels[0].city],
                ["Stars",       hotels[0].stars ? "★".repeat(Math.min(hotels[0].stars, 5)) : "—"],
                ["Check-in",    hotels[0].check_in],
                ["Check-out",   hotels[0].check_out],
                ["Price/night", hotels[0].price_per_night ? `₹${Number(hotels[0].price_per_night).toLocaleString()}` : "—"],
              ].map(([label, val]) => (
                <div key={label as string}>
                  <span style={{ fontSize: 11, color: "rgba(150,175,210,0.45)", display: "block", marginBottom: 3 }}>{label}</span>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#f0f4ff", margin: 0 }}>{val || "—"}</p>
                </div>
              ))}
            </div>
            {hotels[0].booking_url && (
              <a href={hotels[0].booking_url} target="_blank" rel="noopener noreferrer"
                style={{
                  display: "inline-block", marginTop: 16,
                  background: "#6b7ff5", color: "#fff",
                  fontSize: 12, fontWeight: 700,
                  padding: "8px 16px", borderRadius: 10,
                  textDecoration: "none",
                }}>
                Book Hotel →
              </a>
            )}
          </div>
        )}

        {/* Places */}
        {places.length > 0 && (
          <div style={{ background: "#0e1520", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: 20 }}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "#f5a623", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
              Places to Visit
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {places.slice(0, 5).map((p: any, i: number) => (
                <div key={i} style={{ paddingBottom: i < 4 ? 12 : 0, borderBottom: i < 4 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#f0f4ff", margin: "0 0 4px" }}>
                    {p.name || p.place_name}
                  </p>
                  {(p.description || p.summary) && (
                    <p style={{ fontSize: 12, color: "rgba(150,175,210,0.5)", margin: 0 }}>
                      {(p.description || p.summary).slice(0, 150)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div style={{
          background: "linear-gradient(135deg, rgba(107,127,245,0.12), rgba(14,196,168,0.08))",
          border: "1px solid rgba(107,127,245,0.2)",
          borderRadius: 16, padding: 24, textAlign: "center",
        }}>
          <p style={{ fontSize: 14, color: "rgba(200,215,240,0.7)", marginBottom: 14 }}>
            Plan your own trip with AI in seconds
          </p>
          <a href="/"
            style={{
              display: "inline-block",
              background: "linear-gradient(135deg, #0ec4a8, #6b7ff5)",
              color: "#080c14",
              fontSize: 13, fontWeight: 700,
              padding: "10px 24px", borderRadius: 12,
              textDecoration: "none",
            }}>
            Try TravelGuru Free →
          </a>
        </div>

      </div>
    </div>
  );
}