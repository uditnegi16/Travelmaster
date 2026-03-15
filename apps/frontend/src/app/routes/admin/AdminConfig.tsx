import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { Save } from "lucide-react";

interface ConfigRow {
  key: string;
  value: string;
  description: string | null;
  updated_at: string;
}

export default function AdminConfig() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<ConfigRow[]>([]);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      const res = await fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/admin/config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setRows(data);
        const init: Record<string, string> = {};
        data.forEach((r: ConfigRow) => { init[r.key] = r.value; });
        setEdits(init);
      }
    })();
  }, []);

  const saveKey = async (key: string) => {
    setSaving(key);
    const token = await getToken();
    await fetch(`${import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"}/admin/config/${key}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ value: edits[key] }),
    });
    setSaving(null);
    setSaved(key);
    setTimeout(() => setSaved(null), 2000);
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl">
      <h1 className="text-2xl font-bold text-white">App Config</h1>
      <p className="text-sm text-gray-500">Edit config values without redeployment. Changes take effect immediately.</p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              {["Key", "Description", "Value", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr key={row.key} className="border-b border-gray-800/50">
                <td className="px-4 py-3 font-mono text-teal-400 text-xs">{row.key}</td>
                <td className="px-4 py-3 text-gray-500 text-xs max-w-xs">{row.description || "—"}</td>
                <td className="px-4 py-3">
                  <input
                    value={edits[row.key] ?? row.value}
                    onChange={e => setEdits(p => ({ ...p, [row.key]: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 text-white text-sm rounded px-3 py-1.5 w-40 outline-none focus:border-teal-500"
                  />
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => saveKey(row.key)}
                    disabled={saving === row.key || edits[row.key] === row.value}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-teal-500/10 text-teal-400 hover:bg-teal-500/20 disabled:opacity-40"
                  >
                    <Save className="w-3 h-3" />
                    {saved === row.key ? "Saved!" : saving === row.key ? "Saving..." : "Save"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}