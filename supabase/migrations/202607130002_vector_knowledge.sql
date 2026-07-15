create extension if not exists vector with schema extensions;

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 160),
  source_url text,
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_chunks (
  id bigint generated always as identity primary key,
  document_id uuid not null references public.knowledge_documents(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null,
  embedding extensions.vector(1536) not null,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create index if not exists knowledge_documents_user_idx
  on public.knowledge_documents(user_id, created_at desc);

create index if not exists knowledge_chunks_user_idx
  on public.knowledge_chunks(user_id);

create index if not exists knowledge_chunks_embedding_hnsw_idx
  on public.knowledge_chunks
  using hnsw (embedding extensions.vector_cosine_ops);

alter table public.knowledge_documents enable row level security;
alter table public.knowledge_chunks enable row level security;

create or replace function public.list_knowledge_documents(p_user_id uuid)
returns table (
  id uuid,
  title text,
  source_url text,
  chunk_count bigint,
  created_at timestamptz
)
language sql
stable
security invoker
set search_path = ''
as $$
  select d.id, d.title, d.source_url, count(c.id), d.created_at
  from public.knowledge_documents d
  left join public.knowledge_chunks c on c.document_id = d.id
  where d.user_id = p_user_id
  group by d.id
  order by d.created_at desc;
$$;

create or replace function public.match_knowledge_chunks(
  p_user_id uuid,
  query_embedding extensions.vector(1536),
  match_threshold float default 0.68,
  match_count integer default 5
)
returns table (
  document_id uuid,
  title text,
  source_url text,
  content text,
  similarity float
)
language sql
stable
security invoker
set search_path = ''
as $$
  select
    d.id,
    d.title,
    d.source_url,
    c.content,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.knowledge_chunks c
  join public.knowledge_documents d on d.id = c.document_id
  where c.user_id = p_user_id
    and 1 - (c.embedding <=> query_embedding) >= match_threshold
  order by c.embedding <=> query_embedding
  limit least(greatest(match_count, 1), 20);
$$;

revoke all on function public.list_knowledge_documents(uuid) from public, anon, authenticated;
revoke all on function public.match_knowledge_chunks(uuid, extensions.vector, float, integer)
  from public, anon, authenticated;

comment on table public.knowledge_chunks is
  'Per-user RAG chunks embedded with text-embedding-3-small (1536 dimensions).';
