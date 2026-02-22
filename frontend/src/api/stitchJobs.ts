import { api } from "./client";
import type {
  StitchJob,
  StitchJobCreate,
  StitchJobListResponse,
  StitchJobListParams,
} from "../types/stitchJob";

export type { StitchJob, StitchJobCreate, StitchJobListResponse, StitchJobListParams };

export const createStitchJob = async (
  projectId: string,
  data: StitchJobCreate
): Promise<StitchJob> => {
  const resp = await api.post(`/projects/${projectId}/stitch-jobs`, data);
  return resp.data;
};

export const listStitchJobs = async (
  projectId: string,
  params?: StitchJobListParams
): Promise<StitchJobListResponse> => {
  const resp = await api.get(`/projects/${projectId}/stitch-jobs`, { params });
  return resp.data;
};

export const getStitchJob = async (
  projectId: string,
  jobId: string
): Promise<StitchJob> => {
  const resp = await api.get(`/projects/${projectId}/stitch-jobs/${jobId}`);
  return resp.data;
};
