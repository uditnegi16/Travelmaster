// src/app/routes/admin/AdminShell.tsx
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useUser, UserButton, useClerk } from "@clerk/clerk-react";
import {
  LayoutDashboard, Users, Activity, Settings, ScrollText, LogOut, Shield
} from "lucide-react";

const NAV = [
  { to: "/admin/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/admin/users",     icon: Users,           label: "Users" },
  { to: "/admin/health",    icon: Activity,        label: "Health" },
  { to: "/admin/config",    icon: Settings,        label: "Config" },
  { to: "/admin/audit",     icon: ScrollText,      label: "Audit Log" },
];

export default function AdminShell() {
const { user } = useUser();
const navigate = useNavigate();
const { signOut } = useClerk();

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-gray-800 flex items-center gap-2">
          <Shield className="w-5 h-5 text-red-400" />
          <span className="font-bold text-sm text-red-400 tracking-widest uppercase">Admin</span>
        </div>

        {/* Nav */}
        <nav className="px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-red-500/10 text-red-400 font-medium"
                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Bottom — user + back to app */}
        <div className="px-3 py-4 border-t border-gray-800 space-y-2">
          <div className="flex items-center gap-3 px-3 py-2">
            <UserButton />
            <div className="text-xs text-gray-500 truncate">
              {user?.primaryEmailAddress?.emailAddress}
            </div>
          </div>
          <button
            onClick={() => navigate("/app/dashboard")}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Back to App
          </button>
          <button
            onClick={() => signOut(() => navigate("/"))}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-red-400 hover:bg-red-500/10 transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-950 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}