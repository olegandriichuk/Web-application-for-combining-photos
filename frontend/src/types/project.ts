export type ProjectRole = 'owner' | 'editor' | 'viewer'

export type DocumentType = 'Map' | 'Aerial photo' | 'Technical drawing' | 'Plan' | 'Other'

export const DOCUMENT_TYPES: DocumentType[] = ['Map', 'Aerial photo', 'Technical drawing', 'Plan', 'Other']

export type FilterField =
  | 'name'
  | 'description'
  | 'region'
  | 'year'
  | 'institution'
  | 'collection'
  | 'document_type'

export type FilterCondition = {
  field: FilterField
  operator: string
  value: string | number | null
}

export type Project = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  region: string | null;
  year: number | null;
  document_type: DocumentType | null;
  institution: string | null;
  collection: string | null;
  is_private: boolean;
  created_at: string;
  photo_count?: number;
  role: ProjectRole;
};

export type ProjectCreate = {
  name: string;
  description?: string;
  region?: string;
  year?: number;
  document_type?: DocumentType;
  institution?: string;
  collection?: string;
  is_private?: boolean;
};

export type ProjectUpdate = Partial<ProjectCreate>;

export type ProjectFilters = {
  conditions?: FilterCondition[]
  /** Logic expression, e.g. "1 AND 2 AND 3" or "(1 OR 2) AND NOT 3" */
  logic?: string
  is_private?: boolean
};
