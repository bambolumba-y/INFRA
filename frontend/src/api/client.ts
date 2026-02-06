import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/* ------------------------------------------------------------------ */
/*  Telegram initData interceptor                                      */
/* ------------------------------------------------------------------ */

let _initDataRaw: string | undefined;

/**
 * Called once during Telegram SDK initialisation to cache the raw
 * initData string so the Axios interceptor can attach it to every
 * outgoing request.
 */
export function setInitDataRaw(raw: string | undefined) {
  if (raw) {
    _initDataRaw = raw;
  }
}

api.interceptors.request.use((config) => {
  if (_initDataRaw) {
    config.headers["X-Telegram-Init-Data"] = _initDataRaw;
  }
  return config;
});

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface NewsItem {
  id: number;
  source_type: string;
  title: string | null;
  summary: string | null;
  sentiment_score: number | null;
  url: string | null;
  created_at: string | null;
}

export interface JobMatch {
  job_id: number;
  title: string;
  company: string;
  match_percentage: number;
  matching_skills: string[];
  missing_skills: string[];
  recommendation: string;
}

export interface ResumeUploadResult {
  id: number;
  extracted_data: Record<string, unknown>;
}

/* ------------------------------------------------------------------ */
/*  API functions                                                      */
/* ------------------------------------------------------------------ */

export async function fetchNews(params?: {
  source_type?: string;
  min_score?: number;
  limit?: number;
}): Promise<NewsItem[]> {
  const { data } = await api.get<NewsItem[]>("/news", { params });
  return data;
}

export async function uploadResume(file: File): Promise<ResumeUploadResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ResumeUploadResult>("/resume/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchJobMatches(): Promise<JobMatch[]> {
  const { data } = await api.get<JobMatch[]>("/jobs/matches");
  return data;
}

export async function saveApiKeys(keys: {
  groq_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
}): Promise<{ status: string }> {
  const { data } = await api.post<{ status: string }>("/settings/keys", keys);
  return data;
}

/* ------------------------------------------------------------------ */
/*  Admin API                                                          */
/* ------------------------------------------------------------------ */

export interface ScrapingSource {
  id: number;
  source_type: string;
  name: string;
  enabled: boolean;
  interval_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface AdminHealth {
  scheduler_running: boolean;
  jobs: { id: string; name: string; next_run: string | null }[];
}

export async function fetchSources(): Promise<ScrapingSource[]> {
  const { data } = await api.get<ScrapingSource[]>("/admin/sources");
  return data;
}

export async function createSource(source: {
  source_type: string;
  name: string;
  enabled?: boolean;
  interval_minutes?: number;
}): Promise<ScrapingSource> {
  const { data } = await api.post<ScrapingSource>("/admin/sources", source);
  return data;
}

export async function updateSource(
  id: number,
  updates: { enabled?: boolean; interval_minutes?: number },
): Promise<ScrapingSource> {
  const { data } = await api.patch<ScrapingSource>(
    `/admin/sources/${id}`,
    updates,
  );
  return data;
}

export async function deleteSource(id: number): Promise<void> {
  await api.delete(`/admin/sources/${id}`);
}

export async function fetchAdminHealth(): Promise<AdminHealth> {
  const { data } = await api.get<AdminHealth>("/admin/health");
  return data;
}
