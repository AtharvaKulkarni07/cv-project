import { useState, useCallback } from "react";
import type { StepData, CompleteEvent, SSEPayload } from "./types";

const API_BASE = "http://localhost:8000";

export function useStitchingPipeline() {
  const [steps, setSteps] = useState<StepData[]>([]);
  const [finalPanorama, setFinalPanorama] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStepName, setCurrentStepName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<number | null>(null);

  const resetResults = useCallback(() => {
    setSteps([]);
    setFinalPanorama(null);
    setElapsed(null);
    setError(null);
    setActiveStep(null);
    setCurrentStepName("");
  }, []);

  const runPipeline = useCallback(
    async (files: File[]) => {
      if (files.length < 2) {
        setError("Please upload at least 2 images.");
        return;
      }

      setLoading(true);
      resetResults();

      const formData = new FormData();
      files.forEach((f) => formData.append("images", f));

      try {
        const res = await fetch(`${API_BASE}/api/stitch/stream`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Pipeline failed");
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error("No readable stream in response.");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith("data: ")) continue;

            const payload: SSEPayload = JSON.parse(line.slice(6));

            if ("event" in payload && payload.event === "error") {
              throw new Error(payload.detail);
            }

            if ("event" in payload && payload.event === "complete") {
              const complete = payload as CompleteEvent;
              setFinalPanorama(`${API_BASE}${complete.final_panorama}`);
              setElapsed(complete.elapsed_seconds);
            } else {
              const step = payload as StepData;
              step.images = step.images.map((url: string) => `${API_BASE}${url}`);
              setSteps((prev) => [...prev, step]);
              setActiveStep(step.step);
              setCurrentStepName(step.name);
            }
          }
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [resetResults]
  );

  return {
    steps,
    finalPanorama,
    elapsed,
    loading,
    currentStepName,
    error,
    activeStep,
    setActiveStep,
    runPipeline,
    resetResults,
    setError,
  };
}