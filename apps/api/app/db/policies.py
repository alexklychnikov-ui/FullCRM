JSONB_SENSITIVE_DATA_POLICY = (
    "JSONB metadata/config/payload/custom fields/settings/diff columns must not store raw secrets, tokens, "
    "refresh tokens, API keys, credentials, or unredacted AI prompts/outputs. Store only non-sensitive config, "
    "redacted summaries, ENV reference names, or encrypted secret reference IDs."
)

TOKEN_STORAGE_POLICY = (
    "Integration and channel token values are out of I2 behavior scope. When implemented, token-bearing columns must "
    "store ENV reference names or encrypted secret reference IDs, never raw tokens in JSONB."
)

AI_LOG_REDACTION_POLICY = (
    "AI logs may store provider/model/action and token counts in I2. Future prompt/output logging must be redacted "
    "before persistence and must not include raw CRM secrets or integration tokens."
)

TENANT_CONSISTENCY_POLICY = (
    "I2 creates the approved full MVP DB baseline with organization_id on tenant-bound tables and organization FKs. "
    "Cross-table tenant consistency for child references is enforced by I3-I5 service-layer ownership guards before "
    "writes and reads; later hardening may add RLS or composite FKs where the query model stabilizes."
)

TABLES_REQUIRING_APP_TENANT_GUARDS = frozenset(
    {
        "auth_sessions",
        "ai_logs",
        "ai_recommendations",
        "audit_logs",
        "communication_threads",
        "communications",
        "customers",
        "deal_stage_history",
        "deals",
        "events",
        "pipeline_stages",
        "role_permissions",
        "sync_cursors",
        "user_roles",
    }
)

POLICY_JSONB_COLUMNS = frozenset(
    {
        "ai_logs.metadata",
        "ai_recommendations.metadata",
        "audit_logs.diff",
        "audit_logs.metadata",
        "channel_accounts.metadata",
        "channel_accounts.settings",
        "communication_threads.metadata",
        "communications.metadata",
        "communications.payload",
        "companies.custom_fields",
        "companies.metadata",
        "customers.custom_fields",
        "customers.metadata",
        "deal_stage_history.metadata",
        "deals.custom_fields",
        "deals.metadata",
        "events.metadata",
        "events.payload",
        "integration_accounts.metadata",
        "integration_accounts.settings",
        "module_toggles.config",
        "organizations.settings",
        "pipeline_stages.metadata",
        "pipelines.metadata",
        "settings.value",
        "sync_cursors.metadata",
        "users.metadata",
    }
)
