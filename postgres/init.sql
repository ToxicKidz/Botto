CREATE TABLE IF NOT EXISTS guilds (
    guild_id bigint NOT NULL,
    prefix text,
    case_insensitive boolean NOT NULL DEFAULT True,
    CONSTRAINT guilds_pk PRIMARY KEY (guild_id)
);

DO $$
BEGIN
    CREATE TYPE case_type AS ENUM (
        'note',
        'warn',
        'mute',
        'ban'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS cases (
    case_id bigint,
    guild_id bigint REFERENCES guilds(guild_id),
    target bigint NOT NULL,
    moderator bigint NOT NULL,
    case_type case_type NOT NULL,
    expired boolean,
    expires_at timestamp,
    reason varchar(150) NOT NULL DEFAULT 'No Reason Provided'
);

CREATE TABLE IF NOT EXISTS users (
    user_id bigint NOT NULL,
    CONSTRAINT users_pk PRIMARY KEY (user_id)
);
