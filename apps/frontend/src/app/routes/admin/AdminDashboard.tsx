import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { Users, Search, TrendingUp, CheckCircle } from "lucide-react";

interface Analytics {
  total_users: number;
  free_users: number;
  premium_users: number;
  total_searches: number;
  searches_today: number;
  agent_success_rate: number;
  top_destinations: { destination: string; count: number }[];
}

export default function AdminDashboard() {
  const { getToken } = useAuth();
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      const res = await fetch("http://127.0.0.1:8000/admin/analytics", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setData(await res.json());
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>;
  if (!data) return <div className="p-8 text-red-400">Failed to load analytics</div>;

  const cards = [
    { label: "Total Users", value: data.total_users, sub: `${data.free_users} free · ${data.premium_users} premium`, icon: Users, color: "text-blue-400" },
    { label: "Total Searches", value: data.total_searches, sub: `${data.searches_today} today`, icon: Search, color: "text-teal-400" },
    { label: "Agent Success Rate", value: `${data.agent_success_rate}%`, sub: "of all searches", icon: CheckCircle, color: "text-green-400" },
    { label: "Premium Users", value: data.premium_users, sub: `${data.total_users ? Math.round(data.premium_users / data.total_users * 100) : 0}% of total`, icon: TrendingUp, color: "text-yellow-400" },
  ];

  return (
    <div className="p-8 space-y-8 max-w-6xl">
      <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map(({ label, value, sub, icon: Icon, color }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <div className={`text-3xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-gray-500 mt-1">{sub}</div>
          </div>
        ))}
      </div>

      {/* Top destinations */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Top Destinations</h2>
        <div className="space-y-3">
          {data.top_destinations.map(({ destination, count }, i) => (
            <div key={destination} className="flex items-center gap-3">
              <span className="text-xs text-gray-600 w-4">{i + 1}</span>
              <div className="flex-1 bg-gray-800 rounded-full h-2">
                <div
                  className="bg-teal-500 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (count / (data.top_destinations[0]?.count || 1)) * 100)}%` }}
                />
              </div>
              <span className="text-sm text-white w-32 truncate">{destination}</span>
              <span className="text-xs text-gray-500">{count}</span>
            </div>
          ))}
          {data.top_destinations.length === 0 && (
            <p className="text-gray-500 text-sm">No data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}