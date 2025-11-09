// frontend/src/api/photos.ts
import { api } from "./client";

export type PhotoItem = {
  id: string;
  original_name: string;
  mime: string;
  size: number;
  created_at: string; // ISO datetime string
};

export const uploadPhotos = async (files: File[]) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const resp = await api.post("/photos", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data.items as string[]; // масив id
};

export const listPhotos = async (limit = 100, offset = 0) => {
  const resp = await api.get("/photos", { params: { limit, offset } });
  return resp.data.items as PhotoItem[];
};

export const photoUrl = (id: string) => {
  // повертає URL для перегляду/завантаження
  return `${api.defaults.baseURL}/photos/${id}`;
};

export const deletePhoto = async (id: string) => {
  const resp = await api.delete(`/photos/${id}`);
  return resp.data;
};
