import { api } from "./client";
import type { PhotoItem } from "../types/photo";

export type { PhotoItem };

export const uploadPhoto = async (projectId: string, file: File) => {
  const form = new FormData();
  form.append("file", file); 

  const resp = await api.post(`/projects/${projectId}/photos`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return resp.data.item as string; // id photo
};

export const listPhotos = async (
  projectId: string,
  limit = 100,
  offset = 0
): Promise<PhotoItem[]> => {
  const resp = await api.get(`/projects/${projectId}/photos`, {
    params: { limit, offset },
  });
  return resp.data.items;
};



export const fetchPhotoUrl = async (
  projectId: string,
  photoId: string
): Promise<string> => {
  const resp = await api.get(`/projects/${projectId}/photos/${photoId}`);
  return resp.data.url as string;
};

export const deletePhoto = async (projectId: string, photoId: string) => {
  const resp = await api.delete(`/projects/${projectId}/photos/${photoId}`);
  return resp.data;
};
