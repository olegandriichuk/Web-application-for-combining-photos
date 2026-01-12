import { api } from "./client";
import type { Project, ProjectCreate } from "../types/project";

export type { Project, ProjectCreate };

export const createProject = async (data: ProjectCreate): Promise<Project> => {
  const resp = await api.post("/projects", data);
  return resp.data;
};

export const listProjects = async (limit = 100, offset = 0): Promise<Project[]> => {
  const resp = await api.get("/projects", { params: { limit, offset } });
  return resp.data;
};

export const getProject = async (projectId: string): Promise<Project> => {
  const resp = await api.get(`/projects/${projectId}`);
  return resp.data;
};

export const deleteProject = async (projectId: string): Promise<void> => {
  await api.delete(`/projects/${projectId}`);
};
