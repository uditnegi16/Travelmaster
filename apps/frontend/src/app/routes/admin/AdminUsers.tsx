import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";

interface User {
  account_id: string;
  name: string;
  email: string;
  tier: string;
  searches_this_month: number;
  is_banned: boolean;
  created_at: string;
}

export default function AdminUsers() {
  const { getToken } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [acting, setActing] = useState<string | null>(null);

  const fetchUsers = async () => {
    const token = await getToken();
    const res = await fetch("http://127.0.0.1:8000/admin/users", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setUsers(await res.json());
    setLoading(false);
  };

  useEffect(() => { fetchUsers(); }, []);

  const patch = async (account_id: string, url: string, body: object) => {
    setActing(account_id);
    const token = await getToken();
    await fetch(url, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    await fetchUsers();
    setActing(null);
  };

  const resetLimit = async (account_id: string) => {
    setActing(account_id);
    const token = await getToken();
    await fetch(`http://127.0.0.1:8000/admin/users/${account_id}/reset-limit`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    await fetchUsers();
    setActing(null);
  };

  const filtered = users.filter(u =>
    (u.name || "").toLowerCase().includes(search.toLowerCase()) ||
    (u.email || "").toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>;

  return (
    <div className="p-8 space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Users <span className="text-gray-500 text-lg font-normal">({users.length})</span></h1>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search name or email..."
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2 w-64 outline-none focus:border-teal-500"
        />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              {["Name", "Email", "Tier", "Searches", "Status", "Actions"].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(u => (
              <tr key={u.account_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="px-4 py-3 text-white">{u.name || "—"}</td>
                <td className="px-4 py-3 text-gray-400">{u.email || "—"}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.tier === "premium" ? "bg-yellow-500/10 text-yellow-400" : "bg-gray-700 text-gray-400"}`}>
                    {u.tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400">{u.searches_this_month}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.is_banned ? "bg-red-500/10 text-red-400" : "bg-green-500/10 text-green-400"}`}>
                    {u.is_banned ? "Banned" : "Active"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      disabled={acting === u.account_id}
                      onClick={() => patch(u.account_id, `http://127.0.0.1:8000/admin/users/${u.account_id}/tier`, { tier: u.tier === "premium" ? "free" : "premium" })}
                      className="text-xs px-2 py-1 rounded bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20 disabled:opacity-50"
                    >
                      {u.tier === "premium" ? "→ Free" : "→ Premium"}
                    </button>
                    <button
                      disabled={acting === u.account_id}
                      onClick={() => patch(u.account_id, `http://127.0.0.1:8000/admin/users/${u.account_id}/ban`, { is_banned: !u.is_banned })}
                      className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 disabled:opacity-50"
                    >
                      {u.is_banned ? "Unban" : "Ban"}
                    </button>
                    <button
                      disabled={acting === u.account_id}
                      onClick={() => resetLimit(u.account_id)}
                      className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 disabled:opacity-50"
                    >
                      Reset
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center text-gray-500 py-8">No users found</div>
        )}
      </div>
    </div>
  );
}