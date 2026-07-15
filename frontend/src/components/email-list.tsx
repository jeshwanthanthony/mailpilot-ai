import { ChevronLeft, ChevronRight, Inbox, LoaderCircle, Search } from "lucide-react";
import { formatEmailTime, initials, senderName } from "@/lib/time";
import type { EmailSummary, MailFilter } from "@/lib/types";

type EmailListProps = {
  emails: EmailSummary[];
  selectedId: string;
  filter: MailFilter;
  query: string;
  loading: boolean;
  hasMore: boolean;
  onQueryChange: (query: string) => void;
  onSelect: (email: EmailSummary) => void;
  onLoadMore: () => void;
};

export function EmailList({
  emails,
  selectedId,
  filter,
  query,
  loading,
  hasMore,
  onQueryChange,
  onSelect,
  onLoadMore,
}: EmailListProps) {
  return (
    <section className="flex h-full w-full min-w-0 flex-col border-r border-[#dce1e7] bg-white md:w-[390px] md:shrink-0">
      <div className="border-b border-[#dce1e7] px-4 pb-3 pt-4">
        <div className="mb-3 flex h-8 items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#20242a]">{filter === "inbox" ? "Inbox" : "Unread"}</h1>
          </div>
          <span className="text-xs font-medium tabular-nums text-[#78828d]">{emails.length} messages</span>
        </div>
        <label className="flex h-10 items-center gap-2 rounded-md border border-[#d5dbe1] bg-[#f8f9fa] px-3 text-[#78828d] focus-within:border-[#176b5b] focus-within:bg-white">
          <Search size={16} />
          <span className="sr-only">Search email</span>
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search mail"
            className="min-w-0 flex-1 bg-transparent text-sm text-[#20242a] outline-none placeholder:text-[#8d96a0]"
          />
          {loading && <LoaderCircle size={15} className="animate-spin" aria-label="Loading" />}
        </label>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {!loading && emails.length === 0 ? (
          <div className="grid h-full min-h-72 place-items-center px-8 text-center">
            <div>
              <span className="mx-auto grid size-10 place-items-center rounded-md bg-[#eef1f4] text-[#65707c]">
                <Inbox size={20} />
              </span>
              <p className="mt-3 text-sm font-semibold text-[#38414a]">No messages found</p>
              <p className="mt-1 text-xs text-[#78828d]">Try a different search or mailbox.</p>
            </div>
          </div>
        ) : (
          emails.map((email) => {
            const selected = email.id === selectedId;
            return (
              <button
                key={email.id}
                type="button"
                onClick={() => onSelect(email)}
                className={`relative flex w-full gap-3 border-b border-[#edf0f2] px-4 py-3.5 text-left transition-colors ${
                  selected ? "bg-[#edf7f4]" : "bg-white hover:bg-[#f7f9fa]"
                }`}
              >
                {selected && <span className="absolute inset-y-0 left-0 w-[3px] bg-[#176b5b]" />}
                <span className="grid size-9 shrink-0 place-items-center rounded-full bg-[#e7ebef] text-xs font-bold text-[#53606c]">
                  {initials(email.sender)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className={`truncate text-sm ${email.is_unread ? "font-bold text-[#20242a]" : "font-medium text-[#46515c]"}`}>
                      {senderName(email.sender)}
                    </span>
                    <span className="ml-auto shrink-0 text-[11px] text-[#818a94]">{formatEmailTime(email.date)}</span>
                  </span>
                  <span className={`mt-0.5 block truncate text-[13px] ${email.is_unread ? "font-semibold text-[#303841]" : "text-[#58636f]"}`}>
                    {email.subject}
                  </span>
                  <span className="mt-1 block overflow-hidden text-ellipsis whitespace-nowrap text-xs text-[#7a848f]">
                    {email.snippet}
                  </span>
                </span>
                {email.is_unread && <span className="mt-1.5 size-2 shrink-0 rounded-full bg-[#176b5b]" aria-label="Unread" />}
              </button>
            );
          })
        )}
      </div>

      <div className="flex h-12 items-center justify-between border-t border-[#dce1e7] px-4">
        <span className="text-[11px] text-[#7a848f]">Showing {emails.length}</span>
        <div className="flex gap-1">
          <button type="button" disabled className="grid size-7 place-items-center rounded text-[#a6adb5]" title="Previous page">
            <ChevronLeft size={16} />
          </button>
          <button
            type="button"
            onClick={onLoadMore}
            disabled={!hasMore || loading}
            className="grid size-7 place-items-center rounded text-[#596570] hover:bg-[#eef1f4] disabled:text-[#c3c8cd]"
            title="Load more"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </section>
  );
}
