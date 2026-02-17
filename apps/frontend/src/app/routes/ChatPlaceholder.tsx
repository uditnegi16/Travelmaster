import { Link } from "react-router-dom";

export default function ChatPlaceholder() {
  return (
    <div className="space-y-4">
      <div className="card p-6">
        <h1 className="text-2xl font-extrabold">Chat</h1>
        <p className="muted mt-2">
          This will become the ChatGPT-like trip planning UI (Phase-2).
        </p>
      </div>

      <div className="card p-6">
        <div className="muted">
          For now, explore existing seeded sessions in Dashboard → open a session.
        </div>
        <div className="mt-4">
          <Link className="btn btn-primary" to="/app/dashboard">
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
