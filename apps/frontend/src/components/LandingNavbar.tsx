export default function LandingNavbar() {
  return (
    <header className="absolute top-0 left-0 right-0 z-20">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 text-white">
        <div className="text-sm font-semibold tracking-wide">Travel</div>

        <nav className="hidden gap-8 text-sm opacity-90 md:flex">
          <a className="hover:opacity-100" href="#home">Home</a>
          <a className="hover:opacity-100" href="#about">About</a>
          <a className="hover:opacity-100" href="#popular">Popular</a>
          <a className="hover:opacity-100" href="#explore">Explore</a>
        </nav>
      </div>
    </header>
  );
}
