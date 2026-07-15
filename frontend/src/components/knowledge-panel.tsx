"use client";

import { useEffect, useState } from "react";
import { BookOpenText, Database, FileText, LoaderCircle, Plus, Trash2 } from "lucide-react";
import { mailApi } from "@/lib/api";
import type { KnowledgeDocument } from "@/lib/types";

const demoDocuments: KnowledgeDocument[] = [
  {
    id: "demo-handbook",
    title: "Customer support handbook",
    source_url: null,
    chunk_count: 8,
    created_at: "2026-07-12T12:00:00Z",
  },
  {
    id: "demo-pricing",
    title: "Product plans and pricing",
    source_url: "https://example.com/pricing",
    chunk_count: 4,
    created_at: "2026-07-11T12:00:00Z",
  },
];

type KnowledgePanelProps = {
  mode: "demo" | "live";
  onError: (message: string) => void;
  onNotice: (message: string) => void;
};

export function KnowledgePanel({ mode, onError, onNotice }: KnowledgePanelProps) {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>(mode === "demo" ? demoDocuments : []);
  const [title, setTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(mode === "live");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (mode === "demo") {
      setDocuments(demoDocuments);
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    mailApi.knowledge
      .list()
      .then((items) => active && setDocuments(items))
      .catch((error: unknown) => active && onError(error instanceof Error ? error.message : "Could not load knowledge"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [mode, onError]);

  async function addDocument(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim() || content.trim().length < 20) return;
    setSaving(true);
    try {
      const document = mode === "demo"
        ? {
            id: `demo-${Date.now()}`,
            title: title.trim(),
            source_url: sourceUrl.trim() || null,
            chunk_count: Math.max(1, Math.ceil(content.length / 900)),
            created_at: new Date().toISOString(),
          }
        : await mailApi.knowledge.create({
            title: title.trim(),
            content: content.trim(),
            ...(sourceUrl.trim() ? { source_url: sourceUrl.trim() } : {}),
          });
      setDocuments((current) => [document, ...current]);
      setTitle("");
      setSourceUrl("");
      setContent("");
      onNotice(mode === "demo" ? "Demo knowledge indexed" : "Knowledge embedded and indexed");
    } catch (error) {
      onError(error instanceof Error ? error.message : "Could not index knowledge");
    } finally {
      setSaving(false);
    }
  }

  async function removeDocument(document: KnowledgeDocument) {
    if (mode === "live" && !window.confirm(`Delete “${document.title}” from reply knowledge?`)) return;
    try {
      if (mode === "live") await mailApi.knowledge.remove(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      onNotice("Knowledge document removed");
    } catch (error) {
      onError(error instanceof Error ? error.message : "Could not remove knowledge");
    }
  }

  return (
    <section className="h-full min-w-0 flex-1 overflow-y-auto bg-[#f8f9fa]">
      <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-md bg-[#dceee9] text-[#176b5b]">
            <BookOpenText size={20} />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-[#20242a]">Reply knowledge</h1>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-[#68737e]">
              Add trusted context that MailPilot AI retrieves with pgvector before writing a reply. Each account has an isolated index.
            </p>
          </div>
        </div>

        <div className="mt-7 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <form onSubmit={addDocument} className="rounded-lg border border-[#dce1e7] bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-bold text-[#303841]">
              <Plus size={17} className="text-[#176b5b]" /> Index a document
            </div>
            <label className="mt-4 block text-xs font-semibold text-[#596570]">
              Title
              <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={160} required className="mt-1.5 h-10 w-full rounded-md border border-[#d5dbe1] px-3 text-sm outline-none focus:border-[#176b5b]" placeholder="Support policies" />
            </label>
            <label className="mt-3 block text-xs font-semibold text-[#596570]">
              Source URL <span className="font-normal text-[#929aa3]">(optional)</span>
              <input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} type="url" className="mt-1.5 h-10 w-full rounded-md border border-[#d5dbe1] px-3 text-sm outline-none focus:border-[#176b5b]" placeholder="https://…" />
            </label>
            <label className="mt-3 block text-xs font-semibold text-[#596570]">
              Content
              <textarea value={content} onChange={(event) => setContent(event.target.value)} minLength={20} maxLength={50000} required className="mt-1.5 h-44 w-full resize-y rounded-md border border-[#d5dbe1] p-3 text-sm leading-6 outline-none focus:border-[#176b5b]" placeholder="Paste verified policies, product details, or team guidance…" />
            </label>
            <button type="submit" disabled={saving || !title.trim() || content.trim().length < 20} className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-[#176b5b] px-4 text-xs font-semibold text-white hover:bg-[#12594c] disabled:opacity-50">
              {saving ? <LoaderCircle size={15} className="animate-spin" /> : <Database size={15} />}
              {saving ? "Embedding" : "Embed and index"}
            </button>
          </form>

          <div>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#303841]">Indexed sources</h2>
              <span className="text-xs text-[#7a848f]">{documents.length} documents</span>
            </div>
            {loading ? (
              <div className="flex items-center gap-2 rounded-lg border border-[#dce1e7] bg-white p-5 text-sm text-[#68737e]"><LoaderCircle size={16} className="animate-spin" /> Loading index</div>
            ) : documents.length ? (
              <div className="space-y-2">
                {documents.map((document) => (
                  <article key={document.id} className="flex items-start gap-3 rounded-lg border border-[#dce1e7] bg-white p-4 shadow-sm">
                    <span className="grid size-8 shrink-0 place-items-center rounded bg-[#eef1f4] text-[#65707c]"><FileText size={16} /></span>
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-sm font-semibold text-[#303841]">{document.title}</h3>
                      <p className="mt-1 text-[11px] text-[#7a848f]">{document.chunk_count} vector chunks · {new Date(document.created_at).toLocaleDateString()}</p>
                      {document.source_url && <a href={document.source_url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-[11px] text-[#176b5b] hover:underline">{document.source_url}</a>}
                    </div>
                    <button type="button" onClick={() => removeDocument(document)} className="grid size-8 place-items-center rounded text-[#8a949e] hover:bg-red-50 hover:text-red-700" title="Delete document"><Trash2 size={15} /></button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-[#cbd2d8] p-8 text-center text-sm text-[#7a848f]">No knowledge indexed yet.</div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
