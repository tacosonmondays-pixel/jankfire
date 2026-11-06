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
  sniper_feats int not null default 0,
  quiz_right  int  not null default 0
);
-- Lock the table down: only the game server (service key) can read or write it. Browsers never talk to it directly.
alter table jf_users enable row level security;

-- Never Landed (finish a match without touching the ground) and the Wings moving to it from Frequent Flyer.
-- Safe to run again: the grandfathering only happens the first time, when the wings_old column gets added,
-- so only players who had Frequent Flyer (1000 km/h) before this update keep the Wings without Never Landed.
alter table jf_users add column if not exists airborne int not null default 0;
do $$ begin
  if not exists (select 1 from information_schema.columns where table_name = 'jf_users' and column_name = 'wings_old') then
    alter table jf_users add column wings_old int not null default 0;
    update jf_users set wings_old = 1 where top_speed >= 1000;
  end if;
end $$;

-- Sniper Royalty (bit flags for its four sniper feats; it unlocks the Golden Sniper). Safe to run again.
alter table jf_users add column if not exists sniper_feats int not null default 0;

-- Smarty Pants (pop quiz questions answered right; 3 unlock the Big Glasses and the Overalls). Safe to run again.
alter table jf_users add column if not exists quiz_right int not null default 0;
