import LandingNavbar from "../../components/LandingNavbar";
import DestinationStrip from "../../components/Destinationtrip";
import DarkButton from "../../components/DarkButton";
import { SignedIn, SignedOut, SignInButton } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

import { useAuth } from "@clerk/clerk-react";
import { Navigate } from "react-router-dom";

const destinations = [
  {
    title: "Croatia",
    image:
      "https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?q=80&w=1200&auto=format&fit=crop",
  },
  {
    title: "Iceland",
    image:
      "https://images.unsplash.com/photo-1469474968028-56623f02e42e?q=80&w=1200&auto=format&fit=crop",
  },
  {
    title: "Italy",
    image:
      "https://images.unsplash.com/photo-1514896856000-91cb6de818e0?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000",
  },
  {
    title: "Spain",
    image:
      "https://images.unsplash.com/photo-1509840841025-9088ba78a826?q=80&w=1200&auto=format&fit=crop",
  },
];


const featured = [
  {
    title: "Mountain Escape",
    country: "Canada",
    image:
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1400&auto=format&fit=crop",
  },
  {
    title: "Forest Trails",
    country: "Ireland",
    image:
      "https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1400&auto=format&fit=crop",
  },
  {
    title: "Lake Retreat",
    country: "Italy",
    image:
      "https://images.unsplash.com/photo-1713279683563-2b5c354810c0?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000",
  },
];


export default function Landing() {
  const { isSignedIn, isLoaded } = useAuth();

  // Optional: avoid flicker while Clerk loads
  if (!isLoaded) return null;

  if (isSignedIn) {
    return <Navigate to="/welcome" replace />;
  }
  return (
    <div className="min-h-screen bg-black text-white" style={{ overflowX: "hidden", width: "100%" }}>
      {/* HERO */}
      <section className="relative min-h-[720px]">
        <LandingNavbar />

        <img
          src="https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=2200&auto=format&fit=crop"
          alt="Hero"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-black/55" />

        <div className="relative mx-auto max-w-6xl px-6 pt-28">
          <div className="max-w-xl">
            <p className="text-sm opacity-90">Welcome to TravelGuru</p>
            <h1 className="mt-3 text-5xl font-extrabold leading-[1.05] md:text-7xl">
              Explore
              <br />
              The World
            </h1>

            <p className="mt-6 text-sm leading-6 opacity-80">
              Live the trips exploring the world, discover paradises, islands,
              mountains and much more, get your trip now.
            </p>

            <div className="mt-7">
                <SignedIn>
                  <Link
                    to="/app/dashboard"
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-md bg-white/10 border border-white/10 hover:bg-white/15 transition"
                  >
                    Open Dashboard →
                  </Link>
                </SignedIn>

                <SignedOut>
                    <SignInButton mode="modal">
                    <button className="px-6 py-3 rounded-md bg-white/10 border border-white/10 hover:bg-white/15 transition">
                      Open Dashboard →
                    </button>
                  </SignInButton>
                </SignedOut>

            </div>
          </div>

          <DestinationStrip items={destinations} />
        </div>
      </section>

      {/* LEARN MORE */}
      <section id="about" className="bg-black py-20">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 md:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold md:text-4xl">
              Learn More
              <br />
              About Travel
            </h2>
            <p className="mt-6 text-sm leading-6 opacity-75">
              All the trips around the world are a great pleasure and happiness
              for anyone, enjoy the sights when you travel the world. Travel
              safely and without worries, get your trip and explore the paradises
              of the world.
            </p>

            <div className="mt-8">
              <DarkButton label="Explore Travel" href="#explore" />
            </div>
          </div>

          <div className="mx-auto w-full max-w-md overflow-hidden rounded-md">
            <img
              src="https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1400&auto=format&fit=crop"
              alt="Learn more"
              className="h-[340px] w-full object-cover"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-black pb-20">
        <div className="mx-auto max-w-6xl px-6">
          <h3 className="text-center text-2xl font-semibold md:text-3xl">
            How it works
          </h3>
          <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-6 opacity-75">
            Phase-1 is a DB-driven travel workspace: create trips, revisit your history,
            and save sessions for later. AI planning will be enabled once the agent layer is ready.
          </p>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">1) Sign in securely</div>
              <p className="mt-2 text-sm opacity-75">
                Use Clerk sign-in/sign-up and access protected app pages.
              </p>
            </div>

            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">2) Create a trip session</div>
              <p className="mt-2 text-sm opacity-75">
                Add route, dates, and budget to create a new trip workspace.
              </p>
            </div>

            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">3) Save for later</div>
              <p className="mt-2 text-sm opacity-75">
                Save/unsave trips and reopen past sessions anytime.
              </p>
            </div>
          </div>
        </div>
      </section>


      {/* TRAVELGURU PLATFORM */}
      <section id="platform" className="bg-black pb-20">
        <div className="mx-auto max-w-6xl px-6">
          <h3 className="text-center text-2xl font-semibold md:text-3xl">
            TravelGuru Platform
          </h3>
          <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-6 opacity-75">
            Phase-1 is fully DB-driven: authentication, dashboard, saved trips, account,
            and session history. AI planning will be enabled once the agent layer is ready.
          </p>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">Secure Authentication</div>
              <p className="mt-2 text-sm opacity-75">
                Clerk-based sign in/sign up with protected app routes.
              </p>
            </div>

            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">Session Dashboard</div>
              <p className="mt-2 text-sm opacity-75">
                View trip sessions and open session details from the dashboard.
              </p>
            </div>

            <div className="rounded-md border border-white/10 bg-white/5 p-6">
              <div className="text-sm font-semibold">Trips Timeline</div>
              <p className="mt-2 text-sm opacity-75">
                Create a trip session and access all past trip plans in one place (ChatGPT-style history).
              </p>
            </div>
          </div>

          <div className="mt-10 flex justify-center gap-3">
            <SignedIn>
              <DarkButton label="Explore the App" href="/app/dashboard" />
              <DarkButton label="Trips" href="/app/trips" />
              <DarkButton label="Saved Trips" href="/app/saved" />
            </SignedIn>

            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-6 py-3 rounded-md bg-white/10 border border-white/10 hover:bg-white/15 transition">
                  Explore the App →
                </button>
              </SignInButton>

              <SignInButton mode="modal">
                <button className="px-6 py-3 rounded-md bg-white/10 border border-white/10 hover:bg-white/15 transition">
                  View Trips →
                </button>
              </SignInButton>
            </SignedOut>
          </div>

        </div>
      </section>

      {/* ENJOY BEAUTY */}
      <section id="popular" className="bg-black pb-28 pt-6">
        <div className="mx-auto max-w-6xl px-6">
          <h3 className="text-center text-2xl font-semibold md:text-3xl">
            Enjoy The Beauty
            <br />
            Of The World
          </h3>

          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {featured.map((x) => (
              <div key={x.title}>
                <div className="overflow-hidden rounded-md">
                  <img
                    src={x.image}
                    alt={x.title}
                    className="h-56 w-full object-cover"
                    loading="lazy"
                  />
                </div>
                <div className="mt-4">
                  <div className="text-sm font-semibold">{x.title}</div>
                  <div className="mt-2 text-xs opacity-70">📍 {x.country}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* BIG BANNER */}
      <section className="relative">
        <img
          src="https://images.unsplash.com/photo-1523961131990-5ea7c61b2107?q=80&w=2200&auto=format&fit=crop"
          alt="Paradises"
          className="h-[460px] w-full object-cover"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-black/40" />
        <div className="absolute inset-0">
          <div className="mx-auto flex h-full max-w-6xl items-end px-6 pb-14">
            <div className="max-w-xl">
              <h3 className="text-3xl font-bold md:text-4xl">
                Explore The
                <br />
                Best Paradises
              </h3>
              <p className="mt-4 text-sm leading-6 opacity-80">
                Exploring paradises such as islands and valleys when traveling
                the world is one of the greatest experiences.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* NEWSLETTER */}
      <section id="explore" className="bg-black py-24">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 md:grid-cols-2">
          <div className="mx-auto w-full max-w-md overflow-hidden rounded-md">
            <img
              src="https://images.unsplash.com/photo-1563820510191-3b4a20c78568?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000"
              alt="Newsletter"
              className="h-[360px] w-full object-cover"
              loading="lazy"
            />
          </div>

          <div>
            <h3 className="text-3xl font-bold md:text-4xl">
              Your Journey
              <br />
              Starts Here
            </h3>
            <p className="mt-5 text-sm leading-6 opacity-75">
              Get up to date with the latest travel and information from us.
            </p>

            <div className="mt-8 max-w-sm">
              <input
                className="w-full rounded-sm bg-white/10 px-4 py-3 text-sm outline-none placeholder:text-white/50 focus:bg-white/15"
                placeholder="Enter your email"
              />
              <button
                className="mt-4 inline-flex w-full items-center justify-center gap-3 rounded-sm bg-white/15 px-5 py-3 text-sm text-white backdrop-blur hover:bg-white/20 transition"
                type="button"
              >
                Subscribe Our Newsletter <span aria-hidden>→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER (simple version like PDF) */}
      <footer className="border-t border-white/10 bg-black py-16">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 md:grid-cols-5">
          <div className="md:col-span-2">
            <div className="text-sm font-semibold">TravelGuru</div>
            <p className="mt-4 text-sm opacity-70">
              Travel with us and explore the world without limits.
            </p>
          </div>

          <div className="text-sm opacity-85">
            <div className="font-semibold">About</div>
            <ul className="mt-4 space-y-2 opacity-75">
              <li>About Us</li>
              <li>Features</li>
              <li>News & Blog</li>
            </ul>
          </div>

          <div className="text-sm opacity-85">
            <div className="font-semibold">Company</div>
            <ul className="mt-4 space-y-2 opacity-75">
              <li>FAQs</li>
              <li>History</li>
              <li>Testimonials</li>
            </ul>
          </div>

          <div className="text-sm opacity-85">
            <div className="font-semibold">Support</div>
            <ul className="mt-4 space-y-2 opacity-75">
              <li>Privacy Policy</li>
              <li>Terms & Services</li>
              <li>Payments</li>
            </ul>
          </div>
        </div>

        <div className="mx-auto mt-12 max-w-6xl px-6 text-xs opacity-60">
          © Copyright 2026. All rights reserved.
        </div>
      </footer>
    </div>
  );
}