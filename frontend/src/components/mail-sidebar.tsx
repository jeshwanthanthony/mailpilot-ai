import { Inbox, LogOut, MailCheck, MailOpen, PlugZap } from "lucide-react";
import type { MailFilter } from "@/lib/types";

type MailSidebarProps = {
  filter: MailFilter;
  unreadCount: number;
  mode: "demo" | "live";
  accountEmail: string;
  connectUrl: string;
  onFilterChange: (filter: MailFilter) => void;
  onLogout: () => void;
};

export function MailSidebar({
  filter,
  unreadCount,
  mode,
  accountEmail,
  connectUrl,
  onFilterChange,
  onLogout,
}: MailSidebarProps) {
  const items: { id: MailFilter; label: string; icon: typeof Inbox; count?: number }[] = [
    { id: "inbox", label: "Inbox", icon: Inbox },
    { id: "unread", label: "Unread", icon: MailOpen, count: unreadCount },
  ];

  return (
    <aside className="hidden h-full w-[224px] shrink-0 border-r border-[#dce1e7] bg-[#eef1f4] lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-2.5 border-b border-[#dce1e7] px-5">
        <span className="grid size-8 place-items-center rounded-md bg-[#176b5b] text-white">
          <MailCheck size={18} strokeWidth={2.3} />
        </span>
        <span className="text-[17px] font-bold text-[#20242a]">MailPilot</span>
      </div>

      <nav className="flex-1 px-3 py-5" aria-label="Mailbox">
        <p className="mb-2 px-2 text-[11px] font-semibold uppercase text-[#78828d]">Mailbox</p>
        <div className="space-y-1">
          {items.map((item) => {
            const Icon = item.icon;
            const active = filter === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onFilterChange(item.id)}
                className={`flex h-10 w-full items-center gap-3 rounded-md px-3 text-sm transition-colors ${
                  active
                    ? "bg-white font-semibold text-[#20242a] shadow-sm"
                    : "text-[#5d6874] hover:bg-white/70 hover:text-[#20242a]"
                }`}
              >
                <Icon size={17} />
                <span>{item.label}</span>
                {typeof item.count === "number" && (
                  <span className="ml-auto min-w-5 text-right text-xs tabular-nums text-[#78828d]">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-[#dce1e7] p-3">
        <div className="mb-3 flex items-center gap-2 px-2">
          <span
            className={`size-2 rounded-full ${mode === "live" ? "bg-emerald-500" : "bg-amber-500"}`}
            aria-hidden="true"
          />
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-[#38414a]">
              {mode === "live" ? accountEmail : "Portfolio demo"}
            </p>
            <p className="text-[11px] text-[#78828d]">{mode === "live" ? "Gmail connected" : "Sample mailbox"}</p>
          </div>
        </div>
        {mode === "live" ? (
          <button
            type="button"
            onClick={onLogout}
            className="flex h-9 w-full items-center gap-2 rounded-md px-2 text-xs font-medium text-[#5d6874] hover:bg-white hover:text-[#20242a]"
          >
            <LogOut size={15} />
            Sign out
          </button>
        ) : connectUrl ? (
          <a
            href={connectUrl}
            className="flex h-9 w-full items-center justify-center gap-2 rounded-md bg-[#20242a] text-xs font-semibold text-white hover:bg-black"
          >
            <PlugZap size={15} />
            Connect Gmail
          </a>
        ) : null}
      </div>
    </aside>
  );
}
