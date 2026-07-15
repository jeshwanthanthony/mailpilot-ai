export type MailFilter = "inbox" | "unread";
export type WorkspaceView = "mail" | "knowledge";
export type DraftTone = "concise" | "friendly" | "professional";

export type EmailSummary = {
  id: string;
  thread_id: string;
  subject: string;
  sender: string;
  date: string;
  snippet: string;
  is_unread: boolean;
  priority?: "urgent" | "high" | "normal" | "low" | null;
  priority_score?: number | null;
  priority_signals?: string[];
};

export type EmailBody = {
  format: "html" | "plain";
  body: string;
};

export type EmailPage = {
  emails: EmailSummary[];
  next_page_token: string | null;
};

export type ConnectionStatus = {
  connected: boolean;
  email: string | null;
  demo_available: boolean;
};

export type DraftReply = {
  message_id: string;
  subject: string;
  reply_to_email: string;
  draft_text: string;
  sources: KnowledgeCitation[];
};

export type KnowledgeDocument = {
  id: string;
  title: string;
  source_url: string | null;
  chunk_count: number;
  created_at: string;
};

export type KnowledgeCitation = {
  document_id: string;
  title: string;
  source_url: string | null;
  content: string;
  similarity: number;
};
