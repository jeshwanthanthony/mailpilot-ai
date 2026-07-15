"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, MailCheck, RefreshCw, WifiOff, X } from "lucide-react";
import { EmailList } from "@/components/email-list";
import { MailSidebar } from "@/components/mail-sidebar";
import { MessagePane } from "@/components/message-pane";
import { apiUrl, mailApi } from "@/lib/api";
import { demoBodies, demoDraft, demoEmails } from "@/lib/demo";
import type { DraftTone, EmailBody, EmailSummary, MailFilter } from "@/lib/types";

type WorkspaceMode = "checking" | "demo" | "live";

function initialMessageId(items: EmailSummary[]): string {
  if (typeof window === "undefined" || !window.matchMedia("(min-width: 768px)").matches) return "";
  return items[0]?.id ?? "";
}

export function MailWorkspace() {
  const [mode, setMode] = useState<WorkspaceMode>("checking");
  const [accountEmail, setAccountEmail] = useState("");
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [filter, setFilter] = useState<MailFilter>("inbox");
  const [query, setQuery] = useState("");
  const [nextToken, setNextToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [body, setBody] = useState<EmailBody | null>(null);
  const [bodyLoading, setBodyLoading] = useState(false);
  const [draftOpen, setDraftOpen] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [draftLoading, setDraftLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [tone, setTone] = useState<DraftTone>("professional");
  const [instructions, setInstructions] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedEmail = useMemo(
    () => emails.find((email) => email.id === selectedId) ?? null,
    [emails, selectedId],
  );

  const visibleEmails = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();
    return emails.filter((email) => {
      if (filter === "unread" && !email.is_unread) return false;
      if (mode === "live" || !normalizedQuery) return true;
      return `${email.sender} ${email.subject} ${email.snippet}`.toLowerCase().includes(normalizedQuery);
    });
  }, [emails, filter, mode, query]);

  const loadLiveInbox = useCallback(async (search = "") => {
    setLoading(true);
    setError("");
    try {
      const page = await mailApi.list(search);
      setEmails(page.emails);
      setNextToken(page.next_page_token ?? "");
      setSelectedId((current) =>
        current && page.emails.some((email) => email.id === current)
          ? current
          : initialMessageId(page.emails),
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load the inbox");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function initialize() {
      if (!apiUrl) {
        if (!active) return;
        setMode("demo");
        setEmails(demoEmails);
        setSelectedId(initialMessageId(demoEmails));
        setLoading(false);
        return;
      }
      try {
        const status = await mailApi.status();
        if (!active) return;
        if (status.connected) {
          setMode("live");
          setAccountEmail(status.email ?? "Connected account");
          await loadLiveInbox();
        } else {
          setMode("demo");
          setEmails(demoEmails);
          setSelectedId(initialMessageId(demoEmails));
          setLoading(false);
        }
      } catch {
        if (!active) return;
        setMode("demo");
        setEmails(demoEmails);
        setSelectedId(initialMessageId(demoEmails));
        setError("The API is offline, so MailPilot switched to demo data.");
        setLoading(false);
      }
    }
    initialize();
    return () => {
      active = false;
    };
  }, [loadLiveInbox]);

  useEffect(() => {
    if (mode !== "live") return;
    const timeout = window.setTimeout(() => loadLiveInbox(query), 350);
    return () => window.clearTimeout(timeout);
  }, [loadLiveInbox, mode, query]);

  useEffect(() => {
    if (!selectedEmail) {
      setBody(null);
      return;
    }
    setBody(null);
    if (mode === "demo") {
      setBody(demoBodies[selectedEmail.id] ?? { format: "plain", body: selectedEmail.snippet });
      return;
    }
    if (mode !== "live") return;
    let active = true;
    setBodyLoading(true);
    mailApi
      .body(selectedEmail.id)
      .then((value) => {
        if (active) setBody(value);
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError instanceof Error ? requestError.message : "Could not load the message");
      })
      .finally(() => {
        if (active) setBodyLoading(false);
      });
    return () => {
      active = false;
    };
  }, [mode, selectedEmail]);

  function selectEmail(email: EmailSummary) {
    setSelectedId(email.id);
    setDraftOpen(false);
    setDraftText("");
    setInstructions("");
    if (email.is_unread) {
      setEmails((current) =>
        current.map((item) => (item.id === email.id ? { ...item, is_unread: false } : item)),
      );
      if (mode === "live") {
        mailApi.update(email.id, { is_read: true }).catch(() => {
          setError("The message opened, but Gmail did not save its read status.");
        });
      }
    }
  }

  async function loadMore() {
    if (mode !== "live" || !nextToken) return;
    setLoading(true);
    try {
      const page = await mailApi.list(query, nextToken);
      setEmails((current) => [...current, ...page.emails]);
      setNextToken(page.next_page_token ?? "");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load more mail");
    } finally {
      setLoading(false);
    }
  }

  async function archiveSelected() {
    if (!selectedEmail) return;
    const remaining = emails.filter((email) => email.id !== selectedEmail.id);
    setEmails(remaining);
    setSelectedId(remaining[0]?.id ?? "");
    setNotice("Message archived");
    if (mode === "live") {
      try {
        await mailApi.update(selectedEmail.id, { archive: true });
      } catch (requestError) {
        setEmails(emails);
        setSelectedId(selectedEmail.id);
        setError(requestError instanceof Error ? requestError.message : "Could not archive the message");
      }
    }
  }

  async function toggleRead() {
    if (!selectedEmail) return;
    const nextReadState = selectedEmail.is_unread;
    setEmails((current) =>
      current.map((email) =>
        email.id === selectedEmail.id ? { ...email, is_unread: !nextReadState } : email,
      ),
    );
    if (mode === "live") {
      try {
        await mailApi.update(selectedEmail.id, { is_read: nextReadState });
      } catch {
        setError("Gmail did not save the message status.");
      }
    }
  }

  async function generateDraft() {
    if (!selectedEmail) return;
    setDraftLoading(true);
    setError("");
    try {
      if (mode === "demo") {
        await new Promise((resolve) => window.setTimeout(resolve, 500));
        setDraftText(demoDraft(selectedEmail, tone));
      } else {
        const response = await mailApi.draft(selectedEmail.id, tone, instructions);
        setDraftText(response.draft_text);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not generate a draft");
    } finally {
      setDraftLoading(false);
    }
  }

  async function sendReply() {
    if (!selectedEmail || !draftText.trim()) return;
    if (mode === "live" && !window.confirm("Send this reply through Gmail?")) return;
    setSending(true);
    setError("");
    try {
      if (mode === "demo") await new Promise((resolve) => window.setTimeout(resolve, 500));
      else await mailApi.send(selectedEmail.id, draftText);
      setNotice(mode === "demo" ? "Demo reply completed" : "Reply sent");
      setDraftOpen(false);
      setDraftText("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not send the reply");
    } finally {
      setSending(false);
    }
  }

  async function logout() {
    try {
      await mailApi.logout();
      setMode("demo");
      setAccountEmail("");
      setEmails(demoEmails);
      setSelectedId(initialMessageId(demoEmails));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not sign out");
    }
  }

  if (mode === "checking") {
    return (
      <main className="grid h-dvh place-items-center bg-[#f4f6f8]">
        <div className="flex items-center gap-3 text-sm font-semibold text-[#46515c]">
          <span className="grid size-9 place-items-center rounded-md bg-[#176b5b] text-white">
            <MailCheck size={19} />
          </span>
          Opening MailPilot
        </div>
      </main>
    );
  }

  return (
    <main className="h-dvh overflow-hidden bg-[#f4f6f8] text-[#20242a]">
      <div className="flex h-full">
        <MailSidebar
          filter={filter}
          unreadCount={emails.filter((email) => email.is_unread).length}
          mode={mode}
          accountEmail={accountEmail}
          connectUrl={mailApi.connectUrl}
          onFilterChange={setFilter}
          onLogout={logout}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[#dce1e7] bg-white px-4 lg:hidden">
            <span className="grid size-8 place-items-center rounded-md bg-[#176b5b] text-white">
              <MailCheck size={17} />
            </span>
            <span className="font-bold">MailPilot</span>
            <span className={`ml-auto rounded px-2 py-1 text-[10px] font-bold uppercase ${mode === "live" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
              {mode}
            </span>
            <button type="button" onClick={() => (mode === "live" ? loadLiveInbox(query) : setEmails([...demoEmails]))} className="grid size-8 place-items-center rounded-md text-[#65707c] hover:bg-[#eef1f4]" title="Refresh inbox">
              <RefreshCw size={16} />
            </button>
          </header>

          {error && (
            <div className="flex min-h-10 shrink-0 items-center gap-2 border-b border-red-200 bg-red-50 px-4 py-2 text-xs text-red-800">
              {error.includes("offline") ? <WifiOff size={15} /> : <AlertCircle size={15} />}
              <span className="min-w-0 flex-1">{error}</span>
              <button type="button" onClick={() => setError("")} className="grid size-6 place-items-center rounded hover:bg-red-100" title="Dismiss">
                <X size={14} />
              </button>
            </div>
          )}

          <div className="flex min-h-0 flex-1">
            <div className={`${selectedEmail ? "hidden md:flex" : "flex"} h-full w-full md:w-auto`}>
              <EmailList
                emails={visibleEmails}
                selectedId={selectedId}
                filter={filter}
                query={query}
                loading={loading}
                hasMore={mode === "live" && Boolean(nextToken)}
                onQueryChange={setQuery}
                onSelect={selectEmail}
                onLoadMore={loadMore}
              />
            </div>
            <div className={`${selectedEmail ? "flex" : "hidden md:flex"} h-full min-w-0 flex-1`}>
              <MessagePane
                email={selectedEmail}
                body={body}
                bodyLoading={bodyLoading}
                draftText={draftText}
                draftOpen={draftOpen}
                draftLoading={draftLoading}
                sending={sending}
                tone={tone}
                instructions={instructions}
                onBack={() => setSelectedId("")}
                onArchive={archiveSelected}
                onToggleRead={toggleRead}
                onDraftOpen={() => setDraftOpen(true)}
                onDraftClose={() => setDraftOpen(false)}
                onDraftChange={setDraftText}
                onToneChange={setTone}
                onInstructionsChange={setInstructions}
                onGenerate={generateDraft}
                onCopy={() => navigator.clipboard.writeText(draftText)}
                onSend={sendReply}
              />
            </div>
          </div>
        </div>
      </div>

      {notice && (
        <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md bg-[#20242a] px-4 py-2 text-xs font-semibold text-white shadow-lg" role="status">
          {notice}
          <button type="button" onClick={() => setNotice("")} className="ml-3 text-white/70 hover:text-white" aria-label="Dismiss notification">
            <X size={13} />
          </button>
        </div>
      )}
    </main>
  );
}
