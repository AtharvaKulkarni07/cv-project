"use client";

import type { StepData } from "./types";
import { STEP_COLORS, STEP_BG } from "./theme";

interface StepCardProps {
  step: StepData;
  onImageClick: (url: string) => void;
}

export default function StepCard({ step, onImageClick }: StepCardProps) {
  const borderColor = STEP_COLORS[step.step] || "border-white/10";
  const bgGradient = STEP_BG[step.step] || "from-white/5 to-transparent";

  const gridCols =
    step.images.length === 1
      ? "grid-cols-1"
      : step.images.length === 2
      ? "grid-cols-1 md:grid-cols-2"
      : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3";

  return (
    <div
      className={`border ${borderColor} rounded-2xl overflow-hidden bg-gradient-to-b ${bgGradient} transition-all duration-500`}
    >
      <div className="px-6 py-5 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <StepIcon step={step.step} />
            <div>
              <h3 className="text-lg font-bold text-white">{step.name}</h3>
              {step.algorithm && (
                <span className="badge badge-sm bg-white/10 text-white/60 border-white/10 mt-1">
                  {step.algorithm}
                </span>
              )}
            </div>
          </div>
          <div className="badge badge-outline text-white/40 border-white/15">
            Step {step.step}
          </div>
        </div>
        <p className="text-white/40 text-sm mt-3 leading-relaxed">
          {step.description}
        </p>
      </div>

      <div className="p-4">
        <div className={`grid gap-3 ${gridCols}`}>
          {step.images.map((imgUrl, i) => (
            <div
              key={i}
              className="relative group rounded-xl overflow-hidden border border-white/5 bg-black/30 cursor-pointer hover:border-white/20 transition-all duration-300"
              onClick={() => onImageClick(imgUrl)}
            >
              <img
                src={imgUrl}
                alt={`${step.name} output ${i + 1}`}
                className="w-full h-auto object-contain"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-center pb-3">
                <span className="text-white/80 text-xs font-medium">
                  Click to expand
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {step.metadata && Object.keys(step.metadata).length > 0 && (
        <div className="px-6 py-4 border-t border-white/5">
          <MetadataItems meta={step.metadata} />
        </div>
      )}
    </div>
  );
}

function StepIcon({ step }: { step: number }) {
  const icons: Record<number, JSX.Element> = {
    0: (
      <svg className="w-6 h-6 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    1: (
      <svg className="w-6 h-6 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    2: (
      <svg className="w-6 h-6 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    3: (
      <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
      </svg>
    ),
    4: (
      <svg className="w-6 h-6 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
      </svg>
    ),
    5: (
      <svg className="w-6 h-6 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    6: (
      <svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  };

  return icons[step] || icons[0];
}

function MetadataItems({ meta }: { meta: Record<string, unknown> }) {
  const elements: React.ReactNode[] = [];

  for (const [key, value] of Object.entries(meta)) {
    if (key === "final_image" || key === "homography") continue;

    const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

    let display: string;
    if (Array.isArray(value)) {
      display =
        value.length <= 6
          ? value
              .map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v)))
              .join(", ")
          : `[${value.length} items]`;
    } else if (typeof value === "object" && value !== null) {
      display = JSON.stringify(value);
    } else {
      display = String(value);
    }

    elements.push(
      <div key={key} className="flex items-center gap-2 text-xs">
        <span className="text-white/30">{label}:</span>
        <span className="text-white/60 font-mono">{display}</span>
      </div>
    );
  }

  return <div className="flex flex-wrap gap-x-6 gap-y-2">{elements}</div>;
}