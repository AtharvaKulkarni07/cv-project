export default function Hero() {
  return (
    <section className="flex-1 flex flex-col items-center justify-center px-6 py-10 w-full text-center z-10 relative">

      <h1 className="flex flex-col text-6xl sm:text-5xl md:text-6xl lg:text-[5rem] leading-[1.05] mb-8">
        <span className="font-eloquia text-white tracking-tight">Stop editing.</span>
        <span className="font-eurotypo text-orange-500 pr-4">Start orchestrating.</span>
      </h1>

          <p className="text-white/40 text-lg md:text-xl leading-relaxed mb-12 font-light max-w-2xl mx-auto">
        Turn RAW sequences into seamless panoramas
        <br />

        <span className="italic">fast, smart, effortless</span>
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        <a href="/pipeline" className="bg-white text-black px-8 py-4 rounded-full font-bold text-sm hover:bg-gray-200 transition-colors flex items-center gap-2">
          Start stitching 
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
          </svg>
        </a>

      </div>

    </section>
  );
}