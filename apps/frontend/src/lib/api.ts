const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function handle(res: Response) {
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return (await handle(res)) as T;
}

export async function apiPost<T>(path: string, body: any, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
  });
  return (await handle(res)) as T;
}

export async function apiPatch<T>(path: string, token: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
  });
  return (await handle(res)) as T;
}

export async function apiDelete<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return (await handle(res)) as T;
}
