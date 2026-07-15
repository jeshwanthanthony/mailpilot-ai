import type {
  ConnectionStatus,
  DraftReply,
  DraftTone,
  EmailBody,
  EmailPage,
} from "@/lib/types";

export const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (!apiUrl) throw new Error("The API URL is not configured");
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options?.body ? { "Content-Type": "application/json" } : {}),
      ...options?.headers,
    },
  });
  const payload = (await response.json().catch(() => ({}))) as { detail?: string } & T;
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

export const mailApi = {
  connectUrl: apiUrl ? `${apiUrl}/auth/google/start` : "",
  status: () => request<ConnectionStatus>("/auth/status", { cache: "no-store" }),
  list: (query = "", pageToken = "") => {
    const params = new URLSearchParams({ max_results: "25" });
    if (query) params.set("query", query);
    if (pageToken) params.set("page_token", pageToken);
    return request<EmailPage>(`/emails?${params}`, { cache: "no-store" });
  },
  body: (messageId: string) =>
    request<EmailBody>(`/emails/${encodeURIComponent(messageId)}/body`, { cache: "no-store" }),
  update: (messageId: string, action: { is_read?: boolean; archive?: boolean }) =>
    request<{ ok: boolean }>(`/emails/${encodeURIComponent(messageId)}`, {
      method: "PATCH",
      body: JSON.stringify(action),
    }),
  draft: (messageId: string, tone: DraftTone, extraInstructions: string) =>
    request<DraftReply>(`/emails/${encodeURIComponent(messageId)}/draft-reply`, {
      method: "POST",
      body: JSON.stringify({ tone, extra_instructions: extraInstructions }),
    }),
  send: (messageId: string, draftText: string) =>
    request<{ ok: boolean }>(`/emails/${encodeURIComponent(messageId)}/send`, {
      method: "POST",
      body: JSON.stringify({ draft_text: draftText }),
    }),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
};
