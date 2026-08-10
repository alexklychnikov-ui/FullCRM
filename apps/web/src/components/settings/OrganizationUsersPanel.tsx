"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import type { OrganizationRole, OrganizationUser } from "@/lib/api/organizations";
import {
  createOrganizationUser,
  patchOrganizationUser,
  putOrganizationUserRoles,
} from "@/lib/api/organizations";
import { useI18n } from "@/lib/i18n";
import { resolveRoleName } from "@/lib/i18n/labels";

type OrganizationUsersPanelProps = {
  users: OrganizationUser[];
  roles: OrganizationRole[];
  currentUserId: string;
};

export function OrganizationUsersPanel({
  users: initialUsers,
  roles,
  currentUserId,
}: OrganizationUsersPanelProps) {
  const router = useRouter();
  const { t } = useI18n();
  const [users, setUsers] = useState(initialUsers);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [createRoles, setCreateRoles] = useState<string[]>(["manager"]);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, string[]>>(() =>
    Object.fromEntries(initialUsers.map((user) => [user.id, [...user.roles]])),
  );
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const roleNames = useMemo(() => roles.map((role) => role.name), [roles]);

  function toggleCreateRole(roleName: string, enabled: boolean) {
    setCreateRoles((current) => {
      if (enabled) {
        return current.includes(roleName) ? current : [...current, roleName];
      }
      return current.filter((name) => name !== roleName);
    });
  }

  function toggleUserRole(userId: string, roleName: string, enabled: boolean) {
    setRoleDrafts((current) => {
      const existing = current[userId] ?? [];
      const next = enabled
        ? existing.includes(roleName)
          ? existing
          : [...existing, roleName]
        : existing.filter((name) => name !== roleName);
      return { ...current, [userId]: next };
    });
  }

  function upsertUser(next: OrganizationUser) {
    setUsers((current) => {
      const index = current.findIndex((item) => item.id === next.id);
      if (index < 0) {
        return [...current, next].sort((a, b) => a.email.localeCompare(b.email));
      }
      const copy = [...current];
      copy[index] = next;
      return copy;
    });
    setRoleDrafts((current) => ({ ...current, [next.id]: [...next.roles] }));
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (createRoles.length === 0) {
      setError(t("settings.users.rolesRequired"));
      return;
    }

    setPending(true);
    setError("");

    try {
      const created = await createOrganizationUser({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        roles: createRoles,
      });
      upsertUser(created);
      setEmail("");
      setFullName("");
      setPassword("");
      setCreateRoles(["manager"]);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("settings.saveError"));
    } finally {
      setPending(false);
    }
  }

  async function handleSaveRoles(userId: string) {
    const rolesToSave = roleDrafts[userId] ?? [];
    if (rolesToSave.length === 0) {
      setError(t("settings.users.rolesRequired"));
      return;
    }

    setPending(true);
    setError("");

    try {
      const updated = await putOrganizationUserRoles(userId, rolesToSave);
      upsertUser(updated);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("settings.saveError"));
    } finally {
      setPending(false);
    }
  }

  async function handleToggleActive(user: OrganizationUser) {
    if (user.id === currentUserId) {
      setError(t("settings.users.cannotSelfDeactivate"));
      return;
    }

    setPending(true);
    setError("");

    try {
      const updated = await patchOrganizationUser(user.id, { is_active: !user.is_active });
      upsertUser(updated);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("settings.saveError"));
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-8">
      <p className="text-sm text-shell-muted">{t("settings.users.hint")}</p>

      <form className="max-w-xl space-y-3 rounded-md border border-shell-border bg-shell-panel p-4" onSubmit={handleCreate}>
        <h2 className="text-base font-medium text-white">{t("settings.users.createTitle")}</h2>

        <label className="block space-y-1 text-sm">
          <span className="text-shell-muted">{t("login.email")}</span>
          <input
            required
            className="w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-white"
            disabled={pending}
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>

        <label className="block space-y-1 text-sm">
          <span className="text-shell-muted">{t("settings.users.fullName")}</span>
          <input
            required
            className="w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-white"
            disabled={pending}
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
        </label>

        <label className="block space-y-1 text-sm">
          <span className="text-shell-muted">{t("login.password")}</span>
          <input
            required
            minLength={8}
            className="w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-white"
            disabled={pending}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <fieldset className="space-y-2">
          <legend className="text-sm text-shell-muted">{t("settings.users.roles")}</legend>
          <div className="flex flex-wrap gap-3">
            {roleNames.map((roleName) => (
              <label key={roleName} className="flex items-center gap-2 text-sm text-white">
                <input
                  checked={createRoles.includes(roleName)}
                  className="h-4 w-4 accent-shell-accent"
                  disabled={pending}
                  type="checkbox"
                  onChange={(event) => toggleCreateRole(roleName, event.target.checked)}
                />
                {resolveRoleName(roleName, t)}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          className="rounded-md bg-shell-accent px-3 py-2 text-sm text-white disabled:opacity-60"
          disabled={pending}
          type="submit"
        >
          {pending ? t("settings.saving") : t("settings.users.create")}
        </button>
      </form>

      <div className="space-y-3">
        <h2 className="text-base font-medium text-white">{t("settings.users.listTitle")}</h2>
        <ul className="space-y-3">
          {users.map((user) => {
            const draftRoles = roleDrafts[user.id] ?? user.roles;
            const isSelf = user.id === currentUserId;

            return (
              <li
                key={user.id}
                className="space-y-3 rounded-md border border-shell-border bg-shell-panel px-4 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{user.full_name}</p>
                    <p className="text-xs text-shell-muted">{user.email}</p>
                    <p className="mt-1 text-xs text-shell-muted">
                      {user.is_active ? t("settings.users.active") : t("settings.users.inactive")}
                      {isSelf ? ` · ${t("settings.users.you")}` : ""}
                    </p>
                  </div>
                  <button
                    className="rounded-md border border-shell-border px-3 py-1.5 text-sm text-white disabled:opacity-60"
                    disabled={pending || isSelf}
                    type="button"
                    onClick={() => handleToggleActive(user)}
                  >
                    {user.is_active
                      ? t("settings.users.revoke")
                      : t("settings.users.restore")}
                  </button>
                </div>

                <div className="flex flex-wrap gap-3">
                  {roleNames.map((roleName) => (
                    <label key={`${user.id}-${roleName}`} className="flex items-center gap-2 text-sm text-white">
                      <input
                        checked={draftRoles.includes(roleName)}
                        className="h-4 w-4 accent-shell-accent"
                        disabled={pending}
                        type="checkbox"
                        onChange={(event) =>
                          toggleUserRole(user.id, roleName, event.target.checked)
                        }
                      />
                      {resolveRoleName(roleName, t)}
                    </label>
                  ))}
                </div>

                <button
                  className="rounded-md bg-shell-accent px-3 py-1.5 text-sm text-white disabled:opacity-60"
                  disabled={pending}
                  type="button"
                  onClick={() => handleSaveRoles(user.id)}
                >
                  {t("settings.users.saveRoles")}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}
    </div>
  );
}
