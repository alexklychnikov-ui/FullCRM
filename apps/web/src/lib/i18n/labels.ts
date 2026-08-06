import type { TranslationKey } from "./types";

const STAGE_LABEL_KEYS: Record<string, TranslationKey> = {
  New: "stage.new",
  Qualified: "stage.qualified",
  Won: "stage.won",
};

const MODULE_LABEL_KEYS: Record<string, TranslationKey> = {
  ai: "module.ai",
  analytics: "module.analytics",
  crm: "module.crm",
  communications: "module.communications",
};

const CHANNEL_LABEL_KEYS: Record<string, TranslationKey> = {
  telegram: "comms.channel.telegram",
  gmail: "comms.channel.gmail",
  calendar: "comms.channel.calendar",
  email: "comms.channel.email",
};

const INTEGRATION_MODE_KEYS: Record<string, TranslationKey> = {
  live: "comms.mode.live",
  stub: "comms.mode.stub",
  disabled: "comms.mode.disabled",
};

const AI_MODE_KEYS: Record<string, TranslationKey> = {
  mock: "ai.mode.mock",
  live: "ai.mode.live",
  degraded: "ai.mode.degraded",
  disabled: "ai.mode.disabled",
};

const AI_PRIORITY_KEYS: Record<string, TranslationKey> = {
  high: "ai.priority.high",
  medium: "ai.priority.medium",
  low: "ai.priority.low",
};

const DEFAULT_FULL_NAME_KEYS: Record<string, TranslationKey> = {
  Administrator: "admin.role.admin",
};

const INTEGRATION_REASON_KEYS: Record<string, TranslationKey> = {
  "Polling mode enabled via TELEGRAM_BOT_TOKEN and TELEGRAM_ENABLED":
    "comms.reason.telegramLive",
  "TELEGRAM_BOT_TOKEN is set but TELEGRAM_ENABLED is false":
    "comms.reason.telegramDisabled",
  "Set TELEGRAM_BOT_TOKEN and TELEGRAM_ENABLED=true to enable polling":
    "comms.reason.telegramStub",
  "OAuth/token policy not configured for MVP; use manual email channel entries":
    "comms.reason.gmailStub",
  "OAuth/token policy not configured for MVP; calendar sync deferred":
    "comms.reason.calendarStub",
};

function resolveLabel(
  value: string,
  map: Record<string, TranslationKey>,
  t: (key: TranslationKey) => string,
): string {
  const key = map[value];
  return key ? t(key) : value;
}

export function resolveStageName(stageName: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(stageName, STAGE_LABEL_KEYS, t);
}

export function resolveModuleName(moduleKey: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(moduleKey, MODULE_LABEL_KEYS, t);
}

export function resolveChannelName(channel: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(channel, CHANNEL_LABEL_KEYS, t);
}

export function resolveIntegrationMode(mode: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(mode, INTEGRATION_MODE_KEYS, t);
}

export function resolveIntegrationReason(reason: string, t: (key: TranslationKey) => string): string {
  const key = INTEGRATION_REASON_KEYS[reason];
  return key ? t(key) : reason;
}

export function resolveAiMode(mode: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(mode, AI_MODE_KEYS, t);
}

export function resolveAiPriority(priority: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(priority, AI_PRIORITY_KEYS, t);
}

export function resolveDisplayFullName(fullName: string, t: (key: TranslationKey) => string): string {
  return resolveLabel(fullName, DEFAULT_FULL_NAME_KEYS, t);
}

export function resolveRoleName(role: string, t: (key: TranslationKey) => string): string {
  if (role === "admin") {
    return t("admin.role.admin");
  }
  if (role === "manager") {
    return t("admin.role.manager");
  }
  if (role === "analyst") {
    return t("admin.role.analyst");
  }

  return role;
}
