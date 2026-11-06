-- OVERDUE story saves (TECH_PLAN §7). NOT needed for the slice: until this runs, the server keeps one story save
-- per account in jf_users.inv.story. When the owner is ready: Supabase -> SQL Editor -> New query -> paste -> Run.
-- Safe to run again. After it runs, accounts get 3 save slots; an old inv.story save moves over on its next save.
create table if not exists jf_story (
  name_lower  text not null references jf_users(name_lower) on delete cascade,
  slot        smallint not null check (slot between 0 and 2),
  version     int not null default 1,
  act         smallint not null default 1,
  chapter     text not null default 'return_to_sender',
  playtime    int not null default 0,
  coupons     bigint not null default 0,
  data        jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now(),
  primary key (name_lower, slot)
);
alter table jf_story enable row level security;
alter table jf_users add column if not exists story_act smallint not null default 0;
alter table jf_users add column if not exists bosses_killed int not null default 0;
