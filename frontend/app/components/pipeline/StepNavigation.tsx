"use client";

import type { StepData } from "./types";

interface StepNavigationProps {
  steps: StepData[];
  activeStep: number | null;
  onStepClick: (step: number) => void;
}

export default function StepNavigation({
  steps,
  activeStep,
  onStepClick,
}: StepNavigationProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {steps.map((step) => (
        <button
          key={step.step}
          onClick={() => onStepClick(step.step)}
          className={`btn btn-sm rounded-full whitespace-nowrap transition-all duration-300 ${
            activeStep === step.step
              ? "bg-orange-600 text-white border-orange-600 shadow-[0_0_20px_rgba(234,88,12,0.3)]"
              : "btn-ghost text-white/50 hover:text-white border-white/10"
          }`}
        >
          <span className="mr-1">{step.step + 1}</span>
          {step.name}
        </button>
      ))}
    </div>
  );
}