import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";

interface AuditEntry {
  log_id: string;
  admin_id: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  metadata: Record<string, any>;
  ip_address: string | null;
  created_at: string;
}

const ACTION_COLORS: Record<string, string> = {
  update_tier: "text-yellow-400 bg-yellow-500/10",
  ban_user: "text-red-400 bg-red-500/10",
  unban_user: "text-green-400 bg-green-500/10",
  reset_search_limit: "text-blue-400 bg-blue-500/10",
  update_config: "text-teal-400 bg-teal-500/10",
  add_admin: "text-purple-400 bg-purple-500/10",
};

export default function AdminAuditLog() {
  const { getToken } = useAuth();
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      const res = await fetch("http://127.0.0.1:8000/admin/audit-log", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setLogs(await res.json());
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>;

  return (
    <div className="p-8 space-y-6 max-w-6xl">
      <h1 className="text-2xl font-bold text-white">Audit Log</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              {["Action", "Target", "Details", "IP", "Time"].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.log_id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${ACTION_COLORS[log.action] || "text-gray-400 bg-gray-700"}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">
                  {log.target_type && <span className="text-gray-600">{log.target_type}: </span>}
                  <span className="font-mono">{log.target_id || "—"}</span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs font-mono">
                  {Object.keys(log.metadata || {}).length > 0
                    ? JSON.stringify(log.metadata)
                    : "—"}
                </td>
                <td className="px-4 py-3 text-gray-600 text-xs">{log.ip_address || "—"}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(log.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && (
          <div className="text-center text-gray-500 py-8">No audit entries yet</div>
        )}
      </div>
    </div>
  );
}