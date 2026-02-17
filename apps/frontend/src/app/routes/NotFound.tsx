import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#060913] text-slate-100 flex items-center justify-center">
      <div className="card p-10 text-center max-w-md">
        <h1 className="text-3xl font-extrabold">404</h1>
        <p className="mt-3 text-white/70">Page not found.</p>
        <Link to="/" className="btn btn-primary mt-6 inline-flex">
          Back to Home
        </Link>
      </div>
    </div>
  );
}
