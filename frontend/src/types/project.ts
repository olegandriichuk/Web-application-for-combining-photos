export type ProjectRole = 'owner' | 'editor' | 'viewer'

export type Project = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  photo_count?: number;
  role: ProjectRole;
};

export type ProjectCreate = {
  name: string;
  description?: string;
};
