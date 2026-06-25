-- Run this in the Supabase SQL editor to initialise the schema.

create table if not exists public.users (
    phone_number        text primary key,
    subscription_status boolean not null default false,
    paypal_sub_id       text,
    created_at          timestamptz not null default now()
);

create table if not exists public.claims (
    id               uuid primary key default gen_random_uuid(),
    phone_number     text not null references public.users(phone_number),
    ticket_image_url text not null,
    journey_details  jsonb not null default '{}'::jsonb,
    status           text not null default 'pending'
                        check (status in ('pending', 'approved', 'filed', 'failed')),
    estimated_refund numeric(8, 2) not null default 0,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

-- Auto-update updated_at
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger claims_updated_at
    before update on public.claims
    for each row execute function public.set_updated_at();

-- Storage bucket for ticket images (run via Supabase dashboard or Management API)
-- insert into storage.buckets (id, name, public) values ('ticket-images', 'ticket-images', true);
