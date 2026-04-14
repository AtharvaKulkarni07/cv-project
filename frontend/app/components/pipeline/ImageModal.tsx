"use client";

interface ImageModalProps {
  src: string | null;
  onClose: () => void;
}

export default function ImageModal({ src, onClose }: ImageModalProps) {
  if (!src) return null;

  return (
    <dialog className="modal modal-open" onClick={onClose}>
      <div className="modal-box max-w-[95vw] max-h-[95vh] bg-black/95 border border-white/10 p-2">
        <img
          src={src}
          alt="Expanded view"
          className="w-full h-full object-contain rounded-lg"
        />
      </div>
      <form method="dialog" className="modal-backdrop bg-black/80">
        <button onClick={onClose}>close</button>
      </form>
    </dialog>
  );
}