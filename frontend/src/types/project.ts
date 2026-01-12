export type Project = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  photo_count?: number;
};

export type ProjectCreate = {
  name: string;
  description?: string;
};
