import client from "./client";

export interface Avatar {
  id: string;
  name: string;
  status: "draft" | "generating" | "ready" | "error";
  source_photo_url?: string | null;
  driving_video_url?: string | null;
  loop_video_url?: string | null;
  thumbnail_url?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  message?: string;
  error?: string;
}

export interface GenerationOptions {
  resolution?: string;
  fps?: number;
  loop_method?: string;
  blend_frames?: number;
}

export async function listAvatars(): Promise<Avatar[]> {
  const { data } = await client.get<{ avatars: Avatar[] }>("/avatars");
  return data.avatars;
}

export async function createAvatar(name: string): Promise<Avatar> {
  const { data } = await client.post<Avatar>("/avatars", { name });
  return data;
}

export async function getAvatar(id: string): Promise<Avatar> {
  const { data } = await client.get<Avatar>(`/avatars/${id}`);
  return data;
}

export async function deleteAvatar(id: string): Promise<void> {
  await client.delete(`/avatars/${id}`);
}

export async function uploadSourcePhoto(
  id: string,
  file: File,
): Promise<void> {
  const form = new FormData();
  form.append("photo", file);
  await client.post(`/avatars/${id}/source-photo`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function uploadDrivingVideo(
  id: string,
  file: File | Blob,
): Promise<void> {
  const form = new FormData();
  form.append("video", file, file instanceof File ? file.name : "recording.webm");
  await client.post(`/avatars/${id}/driving-video`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function startGeneration(
  id: string,
  options?: GenerationOptions,
): Promise<{ task_id: string }> {
  const { data } = await client.post<{ task_id: string }>(
    `/avatars/${id}/generate`,
    options,
  );
  return data;
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const { data } = await client.get<TaskStatus>(`/tasks/${taskId}`);
  return data;
}

export function getLoopVideoUrl(id: string): string {
  return `/api/avatars/${id}/loop-video`;
}
