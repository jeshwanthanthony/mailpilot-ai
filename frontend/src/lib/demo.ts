import type { DraftTone, EmailBody, EmailSummary } from "@/lib/types";

const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

export const demoEmails: EmailSummary[] = [
  {
    id: "demo-1",
    thread_id: "thread-1",
    subject: "Final details for Thursday's product review",
    sender: "Maya Chen <maya@northstar.studio>",
    date: minutesAgo(18),
    snippet: "I added the onboarding metrics and the revised rollout timeline. Can you confirm the owners before tomorrow?",
    is_unread: true,
  },
  {
    id: "demo-2",
    thread_id: "thread-2",
    subject: "Interview availability",
    sender: "Daniel Ruiz <daniel@pioneer-labs.com>",
    date: minutesAgo(54),
    snippet: "Thanks for applying to the software engineering role. We'd like to schedule a 30-minute conversation next week.",
    is_unread: true,
  },
  {
    id: "demo-3",
    thread_id: "thread-3",
    subject: "Your July usage report",
    sender: "Orbit Cloud <reports@orbitcloud.dev>",
    date: minutesAgo(190),
    snippet: "Your monthly workspace report is ready. Compute usage decreased 12% while deployment frequency increased.",
    is_unread: false,
  },
  {
    id: "demo-4",
    thread_id: "thread-4",
    subject: "Re: Accessibility audit follow-up",
    sender: "Priya Nair <priya@acme.design>",
    date: minutesAgo(1_460),
    snippet: "The keyboard navigation fixes look good. I left two notes on focus order in the settings dialog.",
    is_unread: false,
  },
  {
    id: "demo-5",
    thread_id: "thread-5",
    subject: "Community demo night confirmation",
    sender: "Build Boston <events@buildboston.org>",
    date: minutesAgo(2_940),
    snippet: "Your project has a spot in next month's demo night. Please send a short description and presenter name.",
    is_unread: true,
  },
  {
    id: "demo-6",
    thread_id: "thread-6",
    subject: "Database migration completed",
    sender: "Supabase <notifications@supabase.com>",
    date: minutesAgo(4_350),
    snippet: "Migration 202607120945_add_connection_index completed successfully in the production project.",
    is_unread: false,
  },
];

export const demoBodies: Record<string, EmailBody> = {
  "demo-1": {
    format: "plain",
    body: "Hi,\n\nI added the onboarding metrics and the revised rollout timeline to the product review deck. The only open item is confirming an owner for the account migration checklist.\n\nCould you review slides 8-12 and send the final owner names before tomorrow afternoon?\n\nThanks,\nMaya",
  },
  "demo-2": {
    format: "plain",
    body: "Hi,\n\nThanks for applying to the software engineering role at Pioneer Labs. We'd like to schedule a 30-minute conversation next week to learn more about your recent projects.\n\nAre you available Tuesday at 11:00 AM or Wednesday at 2:30 PM Eastern?\n\nBest,\nDaniel",
  },
  "demo-3": {
    format: "plain",
    body: "Your July workspace report is ready.\n\nCompute usage decreased 12%, deployment frequency increased 18%, and your team maintained 99.97% availability across 24 services.",
  },
  "demo-4": {
    format: "plain",
    body: "Hi,\n\nThe keyboard navigation fixes look good in the latest build. I left two notes on focus order in the settings dialog and one contrast issue on the disabled state.\n\nOnce those are resolved, the audit is ready to close.\n\nPriya",
  },
  "demo-5": {
    format: "plain",
    body: "Congratulations! Your project has a spot in next month's community demo night. Please send a 60-word project description, presenter name, and GitHub link by Friday.",
  },
  "demo-6": {
    format: "plain",
    body: "Migration 202607120945_add_connection_index completed successfully in the production project. Total duration: 8.4 seconds. No manual action is required.",
  },
};

export function demoDraft(email: EmailSummary, tone: DraftTone): string {
  if (email.id === "demo-2") {
    return tone === "concise"
      ? "Hi Daniel,\n\nThank you for reaching out. Tuesday at 11:00 AM Eastern works well for me. I look forward to speaking with you.\n\nBest,\nJeshwanth"
      : "Hi Daniel,\n\nThank you for the invitation. Tuesday at 11:00 AM Eastern works well for me. I’m looking forward to learning more about the team and sharing more about my recent projects.\n\nBest,\nJeshwanth";
  }
  return "Hi,\n\nThanks for the update. I’ll review the details and follow up with the remaining information by tomorrow afternoon.\n\nBest,\nJeshwanth";
}
