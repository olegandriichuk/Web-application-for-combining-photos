// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

import type { ProjectRole } from './project'

export type ProjectMember = {
  user_id: string
  user_name: string
  user_email: string
  role: ProjectRole
}

export type AddMemberRequest = {
  email: string
  role: 'editor' | 'viewer'
}

export type UpdateMemberRoleRequest = {
  role: 'editor' | 'viewer'
}
