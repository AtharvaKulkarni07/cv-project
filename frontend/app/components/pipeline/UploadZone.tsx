"use client";

import { useCallback } from "react";

interface UploadZoneProps {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  previews: string[];
  files: File[];
  loading: boolean;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDrop: (e: React.DragEvent) => void;
  onClear: () => void;
  onSubmit: () => void;
}

export default function UploadZone({
  fileInputRef,
  previews,
  files,
  loading,
  onFileChange,
  onDrop,
  onClear,
  onSubmit,
}: UploadZoneProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      onDrop(e);
    },
    [onDrop]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  return (
    <div className="mb-12">
      <div
        className="relative border-2 border-dashed border-white/10 hover:border-orange-500/40 rounded-2xl p-10 text-center transition-all duration-500 group cursor-pointer bg-gradient-to-b from-white/[0.02] to-transparent"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={onFileChange}
          className="hidden"
          id="pipeline-upload"
        />
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-white/5 group-hover:bg-orange-500/10 flex items-center justify-center transition-all duration-500">
            <svg
              className="w-8 h-8 text-white/30 group-hover:text-orange-500 transition-colors duration-500"
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
          </div>
          <div>
            <p className="text-white/60 text-lg font-medium">
              Drop images here or{" "}
              <span className="text-orange-500 underline underline-offset-4">
                browse
              </span>
            </p>
            <p className="text-white/25 text-sm mt-1">
              Upload 2 or more overlapping images (left to right order)
            </p>
          </div>
        </div>
      </div>

      {previews.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <p className="text-white/50 text-sm">
              {files.length} image{files.length !== 1 ? "s" : ""} selected
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClear();
              }}
              className="btn btn-ghost btn-xs text-white/40 hover:text-white"
            >
              Clear all
            </button>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {previews.map((src, i) => (
              <div
                key={i}
                className="relative flex-shrink-0 w-32 h-24 rounded-xl overflow-hidden border border-white/10"
              >
                <img
                  src={src}
                  alt={`Preview ${i}`}
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-1 left-1 bg-black/70 text-white/70 text-xs px-1.5 py-0.5 rounded">
                  {i + 1}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {files.length >= 2 && !loading && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={onSubmit}
            className="btn btn-lg bg-orange-600 hover:bg-orange-700 border-none text-white rounded-full px-12 shadow-[0_0_40px_rgba(234,88,12,0.3)] hover:shadow-[0_0_60px_rgba(234,88,12,0.5)] transition-all duration-500"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Run Pipeline
          </button>
        </div>
      )}
    </div>
  );
}