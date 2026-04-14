"use client";

import { useRef, useState, useCallback } from "react";
import {
  UploadZone,
  StepCard,
  StepNavigation,
  LoadingIndicator,
  FinalPanorama,
  ImageModal,
  useStitchingPipeline,
} from "./pipeline";

/**
 * Main orchestrator — manages file state, drives the pipeline hook,
 * and renders upload → progress → results flow.
 */
export default function StitchingPipeline() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [modalImage, setModalImage] = useState<string | null>(null);

  const {
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
  } = useStitchingPipeline();

  // -- File handlers --

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const arr = Array.from(incoming).filter((f) => f.type.startsWith("image/"));
    setFiles((prev) => [...prev, ...arr]);
    arr.forEach((f) => {
      const reader = new FileReader();
      reader.onload = (e) =>
        setPreviews((prev) => [...prev, e.target?.result as string]);
      reader.readAsDataURL(f);
    });
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) addFiles(e.target.files);
    },
    [addFiles]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
    },
    [addFiles]
  );

  const clearFiles = useCallback(() => {
    setFiles([]);
    setPreviews([]);
    resetResults();
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [resetResults]);

  const handleSubmit = useCallback(() => {
    if (files.length < 2) {
      setError("Upload at least 2 images.");
      return;
    }
    runPipeline(files);
  }, [files, runPipeline, setError]);

  // -- Filtered steps for active view --
  const visibleSteps =
    activeStep !== null ? steps.filter((s) => s.step === activeStep) : steps;

  return (
    <div className="w-full max-w-5xl mx-auto px-6">
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl md:text-4xl font-eloquia text-white tracking-tight">
          Stitching Pipeline
        </h1>
        <p className="text-white/40 mt-2 text-sm md:text-base">
          Upload overlapping images and watch each CV step in real-time
        </p>
      </div>

      {/* Upload zone */}
      <UploadZone
        fileInputRef={fileInputRef}
        previews={previews}
        files={files}
        loading={loading}
        onFileChange={handleFileChange}
        onDrop={handleDrop}
        onClear={clearFiles}
        onSubmit={handleSubmit}
      />

      {/* Error alert */}
      {error && (
        <div className="alert bg-red-500/10 border border-red-500/30 text-red-400 mb-8 rounded-xl">
          <svg
            className="w-5 h-5 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <LoadingIndicator currentStepName={currentStepName} steps={steps} />
      )}

      {/* Step navigation pills */}
      {steps.length > 0 && !loading && (
        <div className="mb-8">
          <StepNavigation
            steps={steps}
            activeStep={activeStep}
            onStepClick={(s) =>
              setActiveStep(activeStep === s ? null : s)
            }
          />
        </div>
      )}

      {/* Step cards */}
      {visibleSteps.length > 0 && (
        <div className="flex flex-col gap-6 mb-8">
          {visibleSteps.map((step) => (
            <StepCard
              key={`${step.step}-${step.name}`}
              step={step}
              onImageClick={setModalImage}
            />
          ))}
        </div>
      )}

      {/* Final panorama */}
      {finalPanorama && !loading && (
        <FinalPanorama
          src={finalPanorama}
          elapsed={elapsed}
          onImageClick={setModalImage}
        />
      )}

      {/* Lightbox modal */}
      <ImageModal src={modalImage} onClose={() => setModalImage(null)} />
    </div>
  );
}
