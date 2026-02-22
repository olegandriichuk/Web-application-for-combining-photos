export type PresetName =
  | "debug"
  | "default"
  | "p_100mpx"
  | "p_200mpx"
  | "p_400mpx"
  | "p_normal";

export type SaveFormat = "jp2" | "j2k" | "tiff" | "tif";

export type JobStatus = "queued" | "running" | "finished" | "failed" | "canceled";

export type StitchJob = {
  id: string;
  project_id: string;
  status: JobStatus;
  exp_name: string;
  ref_name: string;
  preset_name: string;
  final_res: [number, number]; // [height, width]
  save_format: string;
  corner_points: [number, number][];
  relative_scale: number;
  photo_ids: string[];
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result_s3_key: string | null;
  error_message: string | null;
};

export type StitchJobCreate = {
  photo_ids: string[];
  exp_name: string;
  ref_name: string;
  preset_name: PresetName;
  final_res: [number, number];
  save_format: SaveFormat;
  corner_points: [number, number][];
  relative_scale: number;
};

export type StitchJobListResponse = {
  items: StitchJob[];
  total: number;
  page: number;
  limit: number;
  pages: number;
};

export type StitchJobListParams = {
  page?: number;
  limit?: number;
  status?: JobStatus;
  from?: string;
  to?: string;
  sort?: "startDateDesc" | "startDateAsc";
};

export const PRESET_OPTIONS: { value: PresetName; label: string }[] = [
  { value: "debug", label: "Debug" },
  { value: "default", label: "Default" },
  { value: "p_100mpx", label: "100 MPX" },
  { value: "p_200mpx", label: "200 MPX" },
  { value: "p_400mpx", label: "400 MPX" },
  { value: "p_normal", label: "Normal" },
];

export const SAVE_FORMAT_OPTIONS: { value: SaveFormat; label: string }[] = [
  { value: "jp2", label: "JPEG 2000 (.jp2)" },
  { value: "j2k", label: "JPEG 2000 (.j2k)" },
  { value: "tiff", label: "TIFF (.tiff)" },
  { value: "tif", label: "TIFF (.tif)" },
];

export const STATUS_LABELS: Record<JobStatus, string> = {
  queued: "Queued",
  running: "Running",
  finished: "Finished",
  failed: "Failed",
  canceled: "Canceled",
};

export const STATUS_COLORS: Record<JobStatus, string> = {
  queued: "#6c757d",
  running: "#0d6efd",
  finished: "#198754",
  failed: "#dc3545",
  canceled: "#6c757d",
};
