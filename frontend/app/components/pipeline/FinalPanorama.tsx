"use client";

interface FinalPanoramaProps {
  src: string;
  elapsed: number | null;
  onImageClick: (url: string) => void;
}

export default function FinalPanorama({
  src,
  elapsed,
  onImageClick,
}: FinalPanoramaProps) {
  return (
    <div className="mt-12 border border-orange-500/30 rounded-2xl overflow-hidden bg-gradient-to-b from-orange-500/5 to-transparent">
      <div className="px-6 py-4 border-b border-orange-500/20 flex items-center justify-between">
        <h3 className="text-xl font-eloquia text-white flex items-center gap-2">
          <svg
            className="w-6 h-6 text-orange-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.5"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          Final Panorama
        </h3>
        {elapsed !== null && (
          <span className="badge badge-outline text-white/40 border-white/15 font-mono text-xs">
            {elapsed}s
          </span>
        )}
      </div>
      <div className="p-4">
        <img
          src={src}
          alt="Final Panorama"
          className="w-full rounded-xl cursor-pointer hover:opacity-90 transition-opacity"
          onClick={() => onImageClick(src)}
        />
      </div>
    </div>
  );
}