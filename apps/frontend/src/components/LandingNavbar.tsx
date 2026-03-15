import { SignedIn, SignedOut, SignInButton } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

export default function LandingNavbar() {
  return (
    <header style={{
      position: "absolute", top: 0, left: 0, right: 0, zIndex: 20,
      width: "100%", boxSizing: "border-box",
    }}>
      <div style={{
        margin: "0 auto", maxWidth: 1152,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "20px 24px", color: "white",
      }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 9,
            background: "linear-gradient(135deg, #7c3aed, #a855f7)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 12px rgba(124,58,237,0.4)",
            flexShrink: 0,
          }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="rgba(255,255,255,0.3)" strokeWidth="1.2"/>
              <path d="M12 3 L14 12 L12 10 L10 12 Z" fill="white"/>
              <path d="M12 21 L10 12 L12 14 L14 12 Z" fill="rgba(255,255,255,0.45)"/>
              <circle cx="12" cy="12" r="1.5" fill="white"/>
            </svg>
          </div>
          <span style={{ fontSize: 15, fontWeight: 800, letterSpacing: "-0.02em" }}>TravelGuru</span>
        </div>

        {/* Nav links */}
        <nav style={{ display: "flex", gap: 32, fontSize: 14, opacity: 0.88 }}>
          {["Home","About","Popular","Explore"].map(l => (
            <a key={l} href={`#${l.toLowerCase()}`}
              style={{ color: "white", textDecoration: "none", transition: "opacity 0.15s" }}
              onMouseEnter={e => (e.currentTarget.style.opacity = "1")}
              onMouseLeave={e => (e.currentTarget.style.opacity = "0.88")}
            >{l}</a>
          ))}
        </nav>

        {/* CTA */}
        <div>
          <SignedIn>
            <Link to="/app/dashboard" style={{
              padding: "9px 20px", borderRadius: 10, fontSize: 13, fontWeight: 700,
              background: "#7c3aed", color: "white", textDecoration: "none",
              boxShadow: "0 2px 12px rgba(124,58,237,0.4)",
            }}>
              Dashboard →
            </Link>
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <button style={{
                padding: "9px 20px", borderRadius: 10, fontSize: 13, fontWeight: 700,
                background: "#7c3aed", color: "white", border: "none", cursor: "pointer",
                boxShadow: "0 2px 12px rgba(124,58,237,0.4)",
              }}>
                Sign In →
              </button>
            </SignInButton>
          </SignedOut>
        </div>
      </div>
    </header>
  );
}