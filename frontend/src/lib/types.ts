export type MailFilter = "inbox" | "unread";
export type DraftTone = "concise" | "friendly" | "professional";

export type EmailSummary = {
  id: string;
  thread_id: string;
  subject: string;
  sender: string;
  date: string;
  snippet: string;
  is_unread: boolean;
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
};
