import { api } from "./client";
import type { Project, ProjectCreate, ProjectUpdate, ProjectFilters } from "../types/project";

export type { Project, ProjectCreate, ProjectUpdate, ProjectFilters };

export const createProject = async (data: ProjectCreate): Promise<Project> => {
  const resp = await api.post("/projects", data);
  return resp.data;
};

export const listProjects = async (
  filters: ProjectFilters = {},
  search = '',
  limit = 100,
  offset = 0,
): Promise<Project[]> => {
  const params: Record<string, string | number | boolean> = { limit, offset };
  if (search) params.search = search;
  if (filters.conditions && filters.conditions.length > 0) {
    params.conditions = JSON.stringify(filters.conditions);
    if (filters.logic) params.logic = filters.logic;
  }
  if (filters.is_private !== undefined) params.is_private = filters.is_private;
  const resp = await api.get("/projects", { params });
  return resp.data;
};

export const getProject = async (projectId: string): Promise<Project> => {
  const resp = await api.get(`/projects/${projectId}`);
  return resp.data;
};

export const updateProject = async (projectId: string, data: ProjectUpdate): Promise<Project> => {
  const resp = await api.patch(`/projects/${projectId}`, data);
  return resp.data;
};

export const deleteProject = async (projectId: string): Promise<void> => {
  await api.delete(`/projects/${projectId}`);
};
