-- HITL — Add Sensitive Data Detection and Model Switch features
-- V2__Add_New_Features.sql
-- {schema} is replaced at runtime from DB_SCHEMA env var

-- Add event_metadata column to hitl_events for storing additional context
ALTER TABLE {schema}.hitl_events 
ADD COLUMN IF NOT EXISTS event_metadata JSONB;

-- Insert Sensitive Data Detection feature
INSERT INTO {schema}.hitl_feature_registry (
    feature_key, feature_name, owner_cap, consumer_cap, executor_cap,
    trigger_type, trigger_config, accepted_action, rejected_action
) VALUES (
    'sensitive_data_detection',
    'Sensitive Data Detection Approval',
    'hitl-service', 'chat-service', 'chat-service',
    'content_analysis',
    '{"patterns": ["email", "phone", "ssn", "credit_card", "api_key"], "confidence_threshold": 0.7}',
    'mask_and_continue',
    'block_message'
) ON CONFLICT (feature_key) DO NOTHING;

-- Insert Model Switch Recommendation feature
INSERT INTO {schema}.hitl_feature_registry (
    feature_key, feature_name, owner_cap, consumer_cap, executor_cap,
    trigger_type, trigger_config, accepted_action, rejected_action
) VALUES (
    'model_switch_recommendation',
    'Model Switch Recommendation',
    'hitl-service', 'chat-service', 'chat-service',
    'complexity_analysis',
    '{"complexity_threshold": 0.8, "suggested_models": ["gpt-4o", "claude-3-opus"], "cost_multiplier": 3}',
    'switch_to_advanced_model',
    'continue_with_current_model'
) ON CONFLICT (feature_key) DO NOTHING;
