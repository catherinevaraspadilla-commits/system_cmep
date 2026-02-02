/**
 * Cliente API centralizado.
 * Ref: docs/source/05_api_y_policy.md — formato de respuesta estandar
 */

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include", // enviar cookies (sesion)
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const body = await res.json();

  if (!res.ok) {
    const error = body.error ?? body;
    throw { status: res.status, ...error, detail: body.detail ?? error.message };
  }

  return body;
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    method: "POST",
    body: formData,
    // No Content-Type header — browser sets multipart boundary automatically
  });

  const body = await res.json();

  if (!res.ok) {
    const error = body.error ?? body;
    throw { status: res.status, ...error, detail: body.detail ?? error.message };
  }

  return body;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) => uploadRequest<T>(path, formData),
};
