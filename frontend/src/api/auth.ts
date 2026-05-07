// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

import { api } from "./client";
import type { RegisterData, LoginData, TokenResponse, User } from "../types/auth";

export type { RegisterData, LoginData, TokenResponse, User };

export interface UpdateUserData {
  name?: string;
  email?: string;
  password?: string;
}

export interface UpdateUserResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export async function register(data: RegisterData): Promise<User> {
  const response = await api.post<User>("/auth/register", data);
  return response.data;
}

export async function login(data: LoginData): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/auth/login", data);
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

export async function updateUser(data: UpdateUserData): Promise<UpdateUserResponse> {
  const response = await api.patch<UpdateUserResponse>("/auth/me", data);
  return response.data;
}

export async function deleteAccount(): Promise<void> {
  await api.delete("/auth/me");
}
