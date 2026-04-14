export interface StepData {
  step: number;
  name: string;
  description: string;
  algorithm?: string;
  images: string[];
  metadata: Record<string, unknown>;
  session_id?: string;
}

export interface CompleteEvent {
  event: "complete";
  final_panorama: string;
  elapsed_seconds: number;
  session_id: string;
}

export type SSEPayload = StepData | CompleteEvent | { event: "error"; detail: string };