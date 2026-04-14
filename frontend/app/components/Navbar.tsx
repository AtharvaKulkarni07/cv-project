export default function Navbar() {
  return (
    <header className="w-full flex items-center justify-between px-6 py-8 md:px-12 lg:px-20 z-50">

      <a href="/" className="flex items-center gap-3 cursor-pointer">
        <div className="w-6 h-6 rounded-md bg-orange-600 flex items-center justify-center shadow-[0_0_20px_rgba(234,88,12,0.5)]">
          <div className="w-2 h-2 bg-white rounded-sm"></div>
        </div>
        <span className="font-eloquia text-2xl tracking-tight text-white">Pano.</span>
      </a>

      <nav className="hidden md:flex items-center gap-10 text-sm font-medium text-white/50">
        <a href="/pipeline" className="hover:text-white transition-colors duration-300">Pipeline</a>
        <a href="/pipeline" className="hover:text-white transition-colors duration-300">Algorithms</a>
        <a href="#" className="hover:text-white transition-colors duration-300">About</a>
      </nav>

    </header>
  );
}