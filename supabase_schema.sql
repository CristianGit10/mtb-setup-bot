-- MTB Setup Bot — Esquema Supabase
-- Ejecutar en el SQL editor de Supabase

create table if not exists users (
    telegram_user_id bigint primary key,
    username text,
    first_name text,

    -- Perfil del rider
    weight_kg numeric,
    discipline text,            -- XC / Trail / Enduro / DH
    bike_type text,             -- double / rigid
    front_width numeric,
    rear_width numeric,
    front_tubeless boolean,
    rear_tubeless boolean,
    front_insert boolean,
    rear_insert boolean,
    fork_brand text,            -- Fox / RockShox / Ohlins / Otra
    fork_travel int,
    shock_type text,            -- Solo Air / DebonAir / Coil / No se / null
    riding_style text,          -- Suave / Agresivo

    -- Plan y uso
    plan text not null default 'free',  -- free / pro / shop
    queries_this_month int not null default 0,
    month_key text,                      -- YYYY-MM
    plan_renewal_at timestamptz,
    lemon_squeezy_customer_id text,
    lemon_squeezy_subscription_id text,
    shop_prefix text,                    -- prefijo personalizado plan tiendas

    profile_updated_at timestamptz,
    created_at timestamptz default now(),

    -- Telegram Stars
    telegram_stars_charge_id text
);

create index if not exists users_lemon_subscription_idx
    on users (lemon_squeezy_subscription_id);

-- Migración por si la tabla ya existía sin la columna
alter table users add column if not exists telegram_stars_charge_id text;
