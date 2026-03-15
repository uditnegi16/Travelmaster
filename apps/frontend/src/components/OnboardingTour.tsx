// src/components/OnboardingTour.tsx
import { useEffect, useState, useRef } from "react";

type TourStep = {
  id: string;
  title: string;
  description: string;
  selector: string;        // CSS selector to highlight
  position: "top" | "bottom" | "left" | "right";
};

const TOUR_STEPS: TourStep[] = [
  {
    id: "logo",
    title: "Welcome to TravelGuru 🧭",
    description: "Your AI-powered travel planner. Let us show you around in 30 seconds.",
    selector: "[data-tour='logo']",
    position: "right",
  },
  {
    id: "dashboard",
    title: "Dashboard",
    description: "Your home base — see trip stats, recent sessions, and popular destinations at a glance.",
    selector: "[data-tour='nav-dashboard']",
    position: "right",
  },
  {
    id: "trips",
    title: "My Trips",
    description: "All your travel sessions live here. Filter, search, and pick up where you left off.",
    selector: "[data-tour='nav-trips']",
    position: "right",
  },
  {
  id: "new-trip",
  title: "Plan a New Trip",
  description: "Hit '+ New Trip' from the Trips page to start an AI chat — describe your trip and the agent finds flights, hotels & places instantly.",
  selector: "[data-tour='nav-trips']",
  position: "right",
},
  {
    id: "saved",
    title: "Saved Trips",
    description: "Bookmark any session to revisit your favourite plans anytime.",
    selector: "[data-tour='nav-saved']",
    position: "right",
  },
  {
    id: "premium",
    title: "Premium",
    description: "Upgrade for 100 AI searches/month, priority agent speed, and group trip planning.",
    selector: "[data-tour='nav-premium']",
    position: "right",
  },
  {
    id: "theme",
    title: "Light / Dark Mode",
    description: "Toggle between light and dark themes — your preference is saved automatically.",
    selector: "[data-tour='theme-toggle']",
    position: "bottom",
  },
  {
    id: "search",
    title: "Search",
    description: "Quickly search across all your trips and destinations from anywhere in the app.",
    selector: "[data-tour='topbar-search']",
    position: "bottom",
  },
];

function getRect(selector: string): DOMRect | null {
  const el = document.querySelector(selector);
  return el ? el.getBoundingClientRect() : null;
}

const PADDING = 10;

export default function OnboardingTour({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [visible, setVisible] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  const current = TOUR_STEPS[step];

  // Measure target element
  useEffect(() => {
    setVisible(false);
    setRect(null);
    let attempts = 0;
    const tryMeasure = () => {
      const r = getRect(current.selector);
      if (r) {
        setRect(r);
        setTimeout(() => setVisible(true), 80);
      } else if (attempts++ < 10) {
        setTimeout(tryMeasure, 150); // retry up to 10x if element not in DOM yet
      } else {
        setTimeout(() => setVisible(true), 80); // show tooltip anyway, centered
      }
    };
    tryMeasure();
    window.addEventListener("resize", tryMeasure);
    return () => window.removeEventListener("resize", tryMeasure);
  }, [step]);

  const next = () => {
    if (step < TOUR_STEPS.length - 1) setStep(s => s + 1);
    else finish();
  };
  const prev = () => { if (step > 0) setStep(s => s - 1); };
  const finish = () => {
    localStorage.setItem("tg-tour-done", "1");
    onDone();
  };

  // Tooltip position calc
  const getTooltipStyle = (): React.CSSProperties => {
    if (!rect || !boxRef.current) return { top: "50%", left: "50%", transform: "translate(-50%,-50%)" };
    const box = boxRef.current.getBoundingClientRect();
    const bw = box.width || 300;
    const bh = box.height || 160;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const gap = 16;

    switch (current.position) {
      case "right": return {
        top: Math.min(Math.max(rect.top + rect.height / 2 - bh / 2, 12), vh - bh - 12),
        left: Math.min(rect.right + gap, vw - bw - 12),
      };
      case "left": return {
        top: Math.min(Math.max(rect.top + rect.height / 2 - bh / 2, 12), vh - bh - 12),
        left: Math.max(rect.left - bw - gap, 12),
      };
      case "bottom": return {
        top: Math.min(rect.bottom + gap, vh - bh - 12),
        left: Math.min(Math.max(rect.left + rect.width / 2 - bw / 2, 12), vw - bw - 12),
      };
      case "top": return {
        top: Math.max(rect.top - bh - gap, 12),
        left: Math.min(Math.max(rect.left + rect.width / 2 - bw / 2, 12), vw - bw - 12),
      };
    }
  };

  // Arrow direction (points from tooltip toward element)
  const arrowStyle = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: "absolute", width: 10, height: 10,
      background: "var(--bg-card)", border: "1px solid var(--border)",
      transform: "rotate(45deg)",
    };
    switch (current.position) {
      case "right":  return { ...base, left: -6,  top: "50%", marginTop: -5, borderRight: "none", borderTop: "none" };
      case "left":   return { ...base, right: -6, top: "50%", marginTop: -5, borderLeft: "none", borderBottom: "none" };
      case "bottom": return { ...base, top: -6,   left: "50%", marginLeft: -5, borderBottom: "none", borderRight: "none" };
      case "top":    return { ...base, bottom: -6, left: "50%", marginLeft: -5, borderTop: "none", borderLeft: "none" };
    }
  };

  return (
    <>
      {/* Dark overlay with spotlight cutout */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 9998,
        pointerEvents: "none",
      }}>
        {/* Overlay pieces around the highlight (4 rects) */}
        {rect && (
          <>
            {/* Top */}
            <div style={{ position: "absolute", inset: 0, bottom: `calc(100% - ${rect.top - PADDING}px)`, background: "rgba(0,0,0,0.55)" }} />
            {/* Bottom */}
            <div style={{ position: "absolute", top: rect.bottom + PADDING, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.55)" }} />
            {/* Left */}
            <div style={{ position: "absolute", top: rect.top - PADDING, left: 0, width: Math.max(0, rect.left - PADDING), height: rect.height + PADDING * 2, background: "rgba(0,0,0,0.55)" }} />
            {/* Right */}
            <div style={{ position: "absolute", top: rect.top - PADDING, left: rect.right + PADDING, right: 0, height: rect.height + PADDING * 2, background: "rgba(0,0,0,0.55)" }} />
            {/* Highlight border ring */}
            <div style={{
              position: "absolute",
              top: rect.top - PADDING, left: rect.left - PADDING,
              width: rect.width + PADDING * 2, height: rect.height + PADDING * 2,
              borderRadius: 12, border: "2px solid var(--purple)",
              boxShadow: "0 0 0 4px var(--purple-glow)",
              transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
            }} />
          </>
        )}
        {!rect && <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.55)" }} />}
      </div>

      {/* Tooltip card */}
      <div
        ref={boxRef}
        style={{
          position: "fixed", zIndex: 9999,
          width: 300,
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 16,
          boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
          padding: "20px 22px",
          opacity: visible ? 1 : 0,
          transform: visible ? "scale(1)" : "scale(0.95)",
          transition: "opacity 0.22s ease, transform 0.22s ease",
          pointerEvents: "all",
          ...getTooltipStyle(),
        }}
      >
        {/* Arrow */}
        <div style={arrowStyle()} />

        {/* Step dots */}
        <div style={{ display: "flex", gap: 5, marginBottom: 14 }}>
          {TOUR_STEPS.map((_, i) => (
            <div key={i} style={{
              width: i === step ? 18 : 6, height: 6, borderRadius: 3,
              background: i === step ? "var(--purple)" : i < step ? "var(--mint)" : "var(--border)",
              transition: "all 0.25s ease",
            }} />
          ))}
        </div>

        {/* Content */}
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
          {current.title}
        </div>
        <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 18 }}>
          {current.description}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <button onClick={finish} style={{
            background: "none", border: "none", fontSize: 12,
            color: "var(--text-muted)", cursor: "pointer", padding: 0,
          }}>
            Skip tour
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            {step > 0 && (
              <button onClick={prev} style={{
                padding: "7px 14px", borderRadius: 9, fontSize: 13, fontWeight: 600,
                background: "var(--bg-elevated)", border: "1px solid var(--border)",
                color: "var(--text-primary)", cursor: "pointer",
              }}>
                ← Back
              </button>
            )}
            <button onClick={next} style={{
              padding: "7px 18px", borderRadius: 9, fontSize: 13, fontWeight: 700,
              background: "var(--purple)", border: "none",
              color: "#fff", cursor: "pointer",
              boxShadow: "0 2px 10px var(--purple-glow)",
            }}>
              {step === TOUR_STEPS.length - 1 ? "Finish 🎉" : "Next →"}
            </button>
          </div>
        </div>

        {/* Step counter */}
        <div style={{ marginTop: 10, fontSize: 11, color: "var(--text-faint)", textAlign: "center" }}>
          {step + 1} of {TOUR_STEPS.length}
        </div>
      </div>
    </>
  );
}