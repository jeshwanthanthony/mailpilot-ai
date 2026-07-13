import {
  Archive,
  ArrowLeft,
  Check,
  Copy,
  LoaderCircle,
  Mail,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { formatEmailTime, initials, senderName } from "@/lib/time";
import type { DraftTone, EmailBody, EmailSummary } from "@/lib/types";

type MessagePaneProps = {
  email: EmailSummary | null;
  body: EmailBody | null;
  bodyLoading: boolean;
  draftText: string;
  draftOpen: boolean;
  draftLoading: boolean;
  sending: boolean;
  tone: DraftTone;
  instructions: string;
  onBack: () => void;
  onArchive: () => void;
  onToggleRead: () => void;
  onDraftOpen: () => void;
  onDraftClose: () => void;
  onDraftChange: (value: string) => void;
  onToneChange: (tone: DraftTone) => void;
  onInstructionsChange: (value: string) => void;
  onGenerate: () => void;
  onCopy: () => void;
  onSend: () => void;
};

export function MessagePane({
  email,
  body,
  bodyLoading,
  draftText,
  draftOpen,
  draftLoading,
  sending,
  tone,
  instructions,
  onBack,
  onArchive,
  onToggleRead,
  onDraftOpen,
  onDraftClose,
  onDraftChange,
  onToneChange,
  onInstructionsChange,
  onGenerate,
  onCopy,
  onSend,
}: MessagePaneProps) {
  if (!email) {
    return (
      <section className="hidden h-full min-w-0 flex-1 place-items-center bg-[#f8f9fa] md:grid">
        <div className="text-center">
          <span className="mx-auto grid size-12 place-items-center rounded-md border border-[#dce1e7] bg-white text-[#6c7782]">
            <Mail size={22} />
          </span>
          <p className="mt-3 text-sm font-semibold text-[#46515c]">Select a message</p>
        </div>
      </section>
    );
  }

  return (
    <section className="flex h-full min-w-0 flex-1 flex-col bg-[#f8f9fa]">
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-[#dce1e7] bg-white px-4">
        <div className="flex items-center gap-1">
          <button type="button" onClick={onBack} className="mr-1 grid size-9 place-items-center rounded-md text-[#5d6874] hover:bg-[#eef1f4] md:hidden" title="Back to inbox">
            <ArrowLeft size={18} />
          </button>
          <button type="button" onClick={onArchive} className="grid size-9 place-items-center rounded-md text-[#5d6874] hover:bg-[#eef1f4]" title="Archive">
            <Archive size={18} />
          </button>
          <button type="button" onClick={onToggleRead} className="grid size-9 place-items-center rounded-md text-[#5d6874] hover:bg-[#eef1f4]" title={email.is_unread ? "Mark as read" : "Mark as unread"}>
            {email.is_unread ? <Mail size={18} /> : <Check size={18} />}
          </button>
        </div>
        <button
          type="button"
          onClick={onDraftOpen}
          className="inline-flex h-9 items-center gap-2 rounded-md bg-[#176b5b] px-3.5 text-xs font-semibold text-white hover:bg-[#12594c]"
        >
          <Sparkles size={15} />
          Draft reply
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <article className="mx-auto w-full max-w-3xl px-5 py-7 sm:px-8 sm:py-9">
          <h2 className="text-balance text-2xl font-bold leading-tight text-[#20242a]">{email.subject}</h2>
          <div className="mt-6 flex items-center gap-3 border-b border-[#e1e5e9] pb-5">
            <span className="grid size-10 shrink-0 place-items-center rounded-full bg-[#dfe5e8] text-xs font-bold text-[#4f5b66]">
              {initials(email.sender)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-[#303841]">{senderName(email.sender)}</p>
              <p className="truncate text-xs text-[#77818c]">{email.sender.match(/<(.+)>/)?.[1] ?? email.sender}</p>
            </div>
            <time className="shrink-0 text-xs text-[#77818c]">{formatEmailTime(email.date)}</time>
          </div>

          <div className="min-h-64 py-6 text-[15px] leading-7 text-[#343d46]">
            {bodyLoading ? (
              <div className="flex items-center gap-2 text-sm text-[#77818c]">
                <LoaderCircle size={17} className="animate-spin" />
                Loading message
              </div>
            ) : body?.format === "html" ? (
              <iframe
                title={email.subject}
                sandbox=""
                srcDoc={`<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;color:#343d46;font-family:Arial,sans-serif;font-size:15px;line-height:1.7}a{color:#176b5b}table{max-width:100%}</style></head><body>${body.body}</body></html>`}
                className="h-[480px] w-full border-0 bg-transparent"
              />
            ) : (
              <p className="whitespace-pre-wrap">{body?.body || email.snippet}</p>
            )}
          </div>
        </article>
      </div>

      {draftOpen && (
        <div className="shrink-0 border-t border-[#ccd3d9] bg-white shadow-[0_-8px_30px_rgba(32,36,42,0.08)]">
          <div className="mx-auto max-w-3xl px-4 py-4 sm:px-8">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-[#176b5b]" />
              <h3 className="text-sm font-bold text-[#303841]">Reply draft</h3>
              <select
                value={tone}
                onChange={(event) => onToneChange(event.target.value as DraftTone)}
                className="ml-2 h-8 rounded-md border border-[#d5dbe1] bg-white px-2 text-xs text-[#46515c]"
                aria-label="Draft tone"
              >
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="concise">Concise</option>
              </select>
              <button type="button" onClick={onDraftClose} className="ml-auto grid size-8 place-items-center rounded-md text-[#6d7782] hover:bg-[#eef1f4]" title="Close draft">
                <X size={17} />
              </button>
            </div>
            <input
              value={instructions}
              onChange={(event) => onInstructionsChange(event.target.value)}
              maxLength={500}
              placeholder="Optional direction"
              className="mt-3 h-9 w-full rounded-md border border-[#d5dbe1] bg-[#f8f9fa] px-3 text-xs text-[#343d46] outline-none placeholder:text-[#929aa3]"
            />
            {draftText ? (
              <textarea
                value={draftText}
                onChange={(event) => onDraftChange(event.target.value)}
                className="mt-2 h-32 w-full resize-none rounded-md border border-[#d5dbe1] p-3 text-sm leading-6 text-[#303841] outline-none"
              />
            ) : (
              <div className="mt-2 grid h-24 place-items-center rounded-md border border-dashed border-[#ccd3d9] bg-[#fafbfb]">
                <button
                  type="button"
                  onClick={onGenerate}
                  disabled={draftLoading}
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-[#cbd2d8] bg-white px-3 text-xs font-semibold text-[#38414a] hover:bg-[#f3f5f6] disabled:opacity-60"
                >
                  {draftLoading ? <LoaderCircle size={15} className="animate-spin" /> : <Sparkles size={15} />}
                  {draftLoading ? "Writing" : "Generate draft"}
                </button>
              </div>
            )}
            {draftText && (
              <div className="mt-2 flex items-center justify-between">
                <button type="button" onClick={onGenerate} disabled={draftLoading} className="text-xs font-semibold text-[#176b5b] hover:text-[#12594c] disabled:opacity-50">
                  Regenerate
                </button>
                <div className="flex gap-2">
                  <button type="button" onClick={onCopy} className="grid size-9 place-items-center rounded-md border border-[#d5dbe1] text-[#596570] hover:bg-[#f3f5f6]" title="Copy draft">
                    <Copy size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={onSend}
                    disabled={sending || !draftText.trim()}
                    className="inline-flex h-9 items-center gap-2 rounded-md bg-[#20242a] px-4 text-xs font-semibold text-white hover:bg-black disabled:opacity-50"
                  >
                    {sending ? <LoaderCircle size={15} className="animate-spin" /> : <Send size={15} />}
                    {sending ? "Sending" : "Send reply"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
