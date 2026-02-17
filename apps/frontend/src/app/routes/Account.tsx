import { useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { apiGet } from "../../lib/api";
import AppShell from "../layout/AppShell";

type UserProfile = {
  account_id: string;
  clerk_user_id: string;
  name?: string | null;
  email?: string | null;
  address?: string | null;
  company?: string | null;
  age?: number | null;
  gender?: string | null;
};

export default function Account() {
  const { getToken, isSignedIn } = useAuth();
  const [me, setMe] = useState<UserProfile | null>(null);

  useEffect(() => {
    (async () => {
      if (!isSignedIn) return;
      const token = await getToken();
      if (!token) return;

      const profile = await apiGet<UserProfile>("/me", token);
      setMe(profile);
    })();
  }, [getToken, isSignedIn]);

  return (
      <div>
        <h1 className="text-2xl font-bold">Account</h1>

        {me ? (
          <div className="mt-6 grid gap-4 text-slate-300">
            <div><strong>Name:</strong> {me.name ?? "—"}</div>
            <div><strong>Email:</strong> {me.email ?? "—"}</div>
            <div><strong>Company:</strong> {me.company ?? "—"}</div>
            <div><strong>Address:</strong> {me.address ?? "—"}</div>
            <div><strong>Age:</strong> {me.age ?? "—"}</div>
            <div><strong>Gender:</strong> {me.gender ?? "—"}</div>
          </div>
        ) : (
          <p className="mt-4 text-slate-400">Loading profile…</p>
        )}
      </div>
  );
}
