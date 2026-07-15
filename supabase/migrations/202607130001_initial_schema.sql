create extension if not exists pgcrypto;

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.gmail_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(id) on delete cascade,
  gmail_address text not null,
  access_token text not null,
  refresh_token text not null,
  token_expiry timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists gmail_connections_address_idx
  on public.gmail_connections(gmail_address);

alter table public.users enable row level security;
alter table public.gmail_connections enable row level security;
