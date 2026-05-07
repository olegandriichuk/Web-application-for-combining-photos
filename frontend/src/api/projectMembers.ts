// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

import { api } from './client'
import type { ProjectMember, AddMemberRequest, UpdateMemberRoleRequest } from '../types/projectMember'

export type { ProjectMember, AddMemberRequest, UpdateMemberRoleRequest }

export const listMembers = async (projectId: string): Promise<ProjectMember[]> => {
  const resp = await api.get(`/projects/${projectId}/members`)
  return resp.data
}

export const addMember = async (projectId: string, data: AddMemberRequest): Promise<ProjectMember> => {
  const resp = await api.post(`/projects/${projectId}/members`, data)
  return resp.data
}

export const updateMemberRole = async (
  projectId: string,
  userId: string,
  data: UpdateMemberRoleRequest,
): Promise<ProjectMember> => {
  const resp = await api.patch(`/projects/${projectId}/members/${userId}`, data)
  return resp.data
}

export const removeMember = async (projectId: string, userId: string): Promise<void> => {
  await api.delete(`/projects/${projectId}/members/${userId}`)
}
