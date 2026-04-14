"use client";

import { STEP_DOT } from "./theme";
import type { StepData } from "./types";

interface LoadingIndicatorProps {
  currentStepName: string;
  steps: StepData[];
}

export default function LoadingIndicator({
  currentStepName,
  steps,
}: LoadingIndicatorProps) {
  return (
    <div className="flex flex-col items-center gap-6 py-16">
      <span className="loading loading-ring loading-lg text-orange-500" />
      <div className="text-center">
        <p className="text-white text-lg font-medium">
          {currentStepName ? `Running: ${currentStepName}…` : "Starting pipeline…"}
        </p>
        <p className="text-white/40 text-sm mt-1">
          Steps appear below as they complete
        </p>
      </div>
      {steps.length > 0 && (
        <div className="flex gap-1.5 items-center">
          {steps.map((s) => (
            <div
              key={s.step}
              className={`w-2.5 h-2.5 rounded-full ${
                STEP_DOT[s.step] || "bg-white/30"
              } animate-pulse`}
            />
          ))}
          <div className="w-2.5 h-2.5 rounded-full bg-white/10 animate-ping" />
        </div>
      )}
    </div>
  );
}