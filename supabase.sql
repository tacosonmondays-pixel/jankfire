-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run.
-- Then give the game server SUPABASE_URL and SUPABASE_SERVICE_KEY (Project Settings -> API).
create table if not exists jf_users (
  name_lower  text primary key,
  name        text not null,
  salt        text not null,
  hash        text not null,
  created_at  timestamptz not null default now(),
  profile     jsonb not null default '{}'::jsonb,
  inv         jsonb not null default '{}'::jsonb,
  crates      int  not null default 1,
  bags        int  not null default 1,
  boxes       int  not null default 1,
  kills       int  not null default 0,
  deaths      int  not null default 0,
  bot_kills   int  not null default 0,
  wins        int  not null default 0,
  best_wave   int  not null default 0,
  top_speed   int  not null default 0,
  xp          int  not null default 0,
  playtime    int  not null default 0,
  void_kills  int  not null default 0,
  headshots   int  not null default 0,
  tbags       int  not null default 0,
  sniper_feats int not null default 0
);
-- Already set up from an older version? This adds what's new (safe to run again).
alter table jf_users add column if not exists sniper_feats int not null default 0;
-- Lock the table down: only the game server (service key) can read or write it. Browsers never talk to it directly.
alter table jf_users enable row level security;
