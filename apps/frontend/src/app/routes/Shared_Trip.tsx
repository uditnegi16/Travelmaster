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
    fetch(`http://127.0.0.1:8000/shared/${token}`)
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
  const budget  = data.budget || {};

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center gap-3">
        <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
          <Plane className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="font-bold text-sm text-white">TravelGuru</span>
        <span className="text-gray-500 text-xs ml-2">Shared Trip Plan</span>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Trip title */}
        <div>
          <h1 className="text-2xl font-bold text-white">
            {sess.from_location || "—"} → {sess.to_location || "—"}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {sess.start_date} – {sess.end_date} · {sess.num_adults || 1} adult(s)
          </p>
        </div>

        {/* Narrative */}
        {data.narrative && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-blue-400 mb-3">Trip Summary</h2>
            <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{data.narrative}</p>
          </div>
        )}

        {/* Top Flight */}
        {flights[0] && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-blue-400 mb-3">Recommended Flight</h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                ["Airline", flights[0].airline || flights[0].carrier],
                ["Departure", (flights[0].departure_time || "").slice(0,16).replace("T"," ")],
                ["Arrival",   (flights[0].arrival_time   || "").slice(0,16).replace("T"," ")],
                ["Duration",  flights[0].duration],
                ["Stops",     flights[0].stops ?? 0],
                ["Price",     flights[0].price ? `₹${Number(flights[0].price).toLocaleString()}` : "—"],
              ].map(([label, val]) => (
                <div key={label as string}>
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-white font-medium">{val || "—"}</p>
                </div>
              ))}
            </div>
            {flights[0].booking_url && (
              <a href={flights[0].booking_url} target="_blank" rel="noopener noreferrer"
                className="mt-3 inline-block bg-teal-600 text-white text-xs px-3 py-1.5 rounded-lg font-semibold hover:bg-teal-500 transition-colors">
                Book Flight →
              </a>
            )}
          </div>
        )}

        {/* Top Hotel */}
        {hotels[0] && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-blue-400 mb-3">Recommended Hotel</h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                ["Name",       hotels[0].name || hotels[0].hotel_name],
                ["City",       hotels[0].city],
                ["Stars",      hotels[0].stars ? "★".repeat(Math.min(hotels[0].stars, 5)) : "—"],
                ["Check-in",   hotels[0].check_in],
                ["Check-out",  hotels[0].check_out],
                ["Price/night", hotels[0].price_per_night ? `₹${Number(hotels[0].price_per_night).toLocaleString()}` : "—"],
              ].map(([label, val]) => (
                <div key={label as string}>
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-white font-medium">{val || "—"}</p>
                </div>
              ))}
            </div>
            {hotels[0].booking_url && (
              <a href={hotels[0].booking_url} target="_blank" rel="noopener noreferrer"
                className="mt-3 inline-block bg-teal-600 text-white text-xs px-3 py-1.5 rounded-lg font-semibold hover:bg-teal-500 transition-colors">
                Book Hotel →
              </a>
            )}
          </div>
        )}

        {/* Places */}
        {places.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-blue-400 mb-3">Places to Visit</h2>
            <div className="space-y-3">
              {places.slice(0, 5).map((p: any, i: number) => (
                <div key={i} className="border-b border-gray-800 pb-2 last:border-0 last:pb-0">
                  <p className="text-sm font-medium text-white">{p.name || p.place_name}</p>
                  {(p.description || p.summary) && (
                    <p className="text-xs text-gray-400 mt-0.5">{(p.description || p.summary).slice(0, 150)}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="bg-blue-950 border border-blue-800 rounded-xl p-5 text-center">
          <p className="text-sm text-blue-200 mb-3">Plan your own trip with AI in seconds</p>
          <a href="/" className="inline-block bg-blue-600 text-white text-sm px-5 py-2 rounded-lg font-semibold hover:bg-blue-500 transition-colors">
            Try TravelGuru Free →
          </a>
        </div>
      </div>
    </div>
  );
}