/* Step-specific color tokens for borders, backgrounds, and dot indicators. */

export const STEP_COLORS: Record<number, string> = {
  0: "border-white/20",
  1: "border-emerald-500/40",
  2: "border-cyan-500/40",
  3: "border-amber-500/40",
  4: "border-violet-500/40",
};

export const STEP_BG: Record<number, string> = {
  0: "from-white/5 to-transparent",
  1: "from-emerald-500/10 to-transparent",
  2: "from-cyan-500/10 to-transparent",
  3: "from-amber-500/10 to-transparent",
  4: "from-violet-500/10 to-transparent",
};

export const STEP_DOT: Record<number, string> = {
  0: "bg-white/50",
  1: "bg-emerald-500",
  2: "bg-cyan-500",
  3: "bg-amber-500",
  4: "bg-violet-500",
};

export const STEP_NAMES: Record<number, string> = {
  0: "Image Load",
  1: "Harris Corners",
  2: "Feature Matching",
  3: "RANSAC Homography",
  4: "Warping & Stitching",
};