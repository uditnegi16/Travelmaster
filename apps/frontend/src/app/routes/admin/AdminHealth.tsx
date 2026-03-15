import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { CheckCircle, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

interface HealthLog {
  service: string;
  status: string;
  response_time_ms: number | null;
  error_message: string | null;
  checked_at: string;
}

export default function AdminHealth() {
  const { getToken } = useAuth();
  const [logs, setLogs] = useState<HealthLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    const token = await getToken();
    const res = await fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/admin/health`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setLogs(await res.json());
    setLoading(false);
    setRefreshing(false);
  };

  const triggerFullCheck = async () => {
    setRefreshing(true);
    const token = await getToken();
    await fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/health/full`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    await fetchHealth();
  };

  useEffect(() => { fetchHealth(); }, []);

  const icon = (status: string) => {
    if (status === "healthy") return <CheckCircle className="w-5 h-5 text-green-400" />;
    if (status === "degraded") return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    return <XCircle className="w-5 h-5 text-red-400" />;
  };

  const color = (status: string) =>
    status === "healthy" ? "text-green-400" : status === "degraded" ? "text-yellow-400" : "text-red-400";

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>;

  return (
    <div className="p-8 space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">System Health</h1>
        <button
          onClick={triggerFullCheck}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-lg text-sm hover:bg-teal-500/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          Run Health Check
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {logs.map(log => (
          <div key={log.service} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-white capitalize">{log.service}</span>
              {icon(log.status)}
            </div>
            <div className={`text-lg font-bold capitalize ${color(log.status)}`}>{log.status}</div>
            {log.response_time_ms !== null && (
              <div className="text-xs text-gray-500 mt-1">{log.response_time_ms}ms response</div>
            )}
            {log.error_message && (
              <div className="text-xs text-red-400 mt-2 truncate">{log.error_message}</div>
            )}
            <div className="text-xs text-gray-600 mt-2">
              {new Date(log.checked_at).toLocaleString()}
            </div>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="col-span-3 text-center text-gray-500 py-8">
            No health logs yet. Click "Run Health Check" to generate.
          </div>
        )}
      </div>
    </div>
  );
}