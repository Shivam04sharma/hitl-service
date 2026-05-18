-- HITL — Chat Compression tables
-- V1__Add_Hitl_Chat_Compression.sql
-- {schema} is replaced at runtime from DB_SCHEMA env var

CREATE TABLE IF NOT EXISTS {schema}.hitl_feature_registry (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_key     VARCHAR(100) NOT NULL UNIQUE,
    feature_name    VARCHAR(255) NOT NULL,
    owner_cap       VARCHAR(50)  NOT NULL,
    consumer_cap    VARCHAR(50)  NOT NULL,
    executor_cap    VARCHAR(50)  NOT NULL,
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    trigger_type    VARCHAR(50)  NOT NULL,
    trigger_config  JSONB        NOT NULL,
    accepted_action TEXT         NOT NULL,
    rejected_action TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.hitl_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT         NOT NULL,
    feature_key     VARCHAR(100) NOT NULL,
    pair_count      INTEGER      NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'shown',
    user_response   VARCHAR(20),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    responded_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_hitl_events_conversation_id
    ON {schema}.hitl_events (conversation_id);

CREATE INDEX IF NOT EXISTS idx_hitl_events_feature_pair
    ON {schema}.hitl_events (conversation_id, pair_count);

INSERT INTO {schema}.hitl_feature_registry (
    feature_key, feature_name, owner_cap, consumer_cap, executor_cap,
    trigger_type, trigger_config, accepted_action, rejected_action
) VALUES (
    'chat_compression',
    'Chat Compression Approval',
    'hitl-service', 'chat-service', 'summarization-service',
    'pair_count',
    '{"thresholds": [10, 20], "hard_limit": 30}',
    'compress_and_save_summary',
    'continue_normal'
) ON CONFLICT (feature_key) DO NOTHING;
