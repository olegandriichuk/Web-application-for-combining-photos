import { api } from "./client";
import type { PhotoItem } from "../types/photo";

export type { PhotoItem };

export const uploadPhoto = async (projectId: string, file: File) => {
  const form = new FormData();
  form.append("file", file); // важливо: ключ "file" має збігатися з бекендом

  const resp = await api.post(`/projects/${projectId}/photos`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return resp.data.item as string; // id фото
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

export const photoUrl = (projectId: string, photoId: string) => {
  return `${api.defaults.baseURL}/projects/${projectId}/photos/${photoId}`;
};

export const fetchPhotoBlob = async (
  projectId: string,
  photoId: string
): Promise<string> => {
  const resp = await api.get(`/projects/${projectId}/photos/${photoId}`, {
    responseType: "blob",
  });
  return URL.createObjectURL(resp.data);
};

export const deletePhoto = async (projectId: string, photoId: string) => {
  const resp = await api.delete(`/projects/${projectId}/photos/${photoId}`);
  return resp.data;
};
