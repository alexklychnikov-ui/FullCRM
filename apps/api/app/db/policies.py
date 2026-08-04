JSONB_SENSITIVE_DATA_POLICY = (
    "JSONB metadata/config/payload/custom fields/settings columns must not store raw secrets, raw tokens, refresh "
    "tokens, API keys, credentials, or copied message bodies beyond a minimal deterministic smoke payload. Store only "
    "non-sensitive config, redacted summaries, or public identifiers needed for baseline checks."
)

TENANT_OWNERSHIP_POLICY = (
    "P2 tenant ownership is enforced with organization_id on every tenant-bound table plus composite foreign keys "
    "for tenant child references. This keeps organization boundaries valid at the database layer even while the UI "
    "stays single-organization in MVP."
)
