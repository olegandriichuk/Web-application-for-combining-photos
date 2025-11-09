import { api } from "./client";

export type Item = { id: number; title: string; description: string };
export type ItemCreate = { title: string; description?: string };
export type ItemUpdate = { title?: string; description?: string };

export const listItems = async (): Promise<Item[]> => {
  const { data } = await api.get("/items");
  return data;
};

export const createItem = async (payload: ItemCreate): Promise<Item> => {
  const { data } = await api.post("/items", payload);
  return data;
};

export const updateItem = async (id: number, payload: ItemUpdate): Promise<Item> => {
  const { data } = await api.patch(`/items/${id}`, payload);
  return data;
};

export const deleteItem = async (id: number): Promise<void> => {
  await api.delete(`/items/${id}`);
};
