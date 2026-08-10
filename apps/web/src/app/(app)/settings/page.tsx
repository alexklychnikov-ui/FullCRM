import { cookies } from "next/headers";

import { OrganizationModulesForm } from "@/components/settings/OrganizationModulesForm";
import { OrganizationSettingsForm } from "@/components/settings/OrganizationSettingsForm";
import { OrganizationUsersPanel } from "@/components/settings/OrganizationUsersPanel";
import { SettingsIntegrationsPanel } from "@/components/settings/SettingsIntegrationsPanel";
import { SettingsTabs, type SettingsTab } from "@/components/settings/SettingsTabs";
import { fetchIntegrationsStatus } from "@/lib/api/communications";
import {
  fetchOrganizationModules,
  fetchOrganizationRoles,
  fetchOrganizationSettings,
  fetchOrganizationUsers,
} from "@/lib/api/organizations";
import { getServerSession } from "@/lib/auth/session";

type SettingsPageProps = {
  searchParams: Promise<{ tab?: string }>;
};

function resolveTab(value: string | undefined): SettingsTab {
  if (value === "analytics" || value === "integrations" || value === "modules") {
    return value;
  }

  return "users";
}

export default async function SettingsPage({ searchParams }: SettingsPageProps) {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  const params = await searchParams;
  const activeTab = resolveTab(params.tab);

  if (!session.permissions.includes("admin.manage")) {
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Настройки</h1>
        <p className="text-sm text-shell-muted">
          Недостаточно прав для управления настройками организации.
        </p>
      </div>
    );
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  const [settingsResult, integrationsResult, modulesResult, usersResult, rolesResult] =
    await Promise.allSettled([
      fetchOrganizationSettings(cookieHeader),
      fetchIntegrationsStatus(cookieHeader),
      fetchOrganizationModules(cookieHeader),
      fetchOrganizationUsers(cookieHeader),
      fetchOrganizationRoles(cookieHeader),
    ]);

  const settings = settingsResult.status === "fulfilled" ? settingsResult.value : null;
  const integrations =
    integrationsResult.status === "fulfilled" ? integrationsResult.value.integrations : null;
  const modules = modulesResult.status === "fulfilled" ? modulesResult.value.modules : null;
  const users = usersResult.status === "fulfilled" ? usersResult.value.users : null;
  const roles = rolesResult.status === "fulfilled" ? rolesResult.value.roles : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Настройки</h1>
        <p className="text-sm text-shell-muted">Люди, аналитика, интеграции и модули</p>
      </div>

      <SettingsTabs activeTab={activeTab} />

      {activeTab === "users" ? (
        users && roles ? (
          <OrganizationUsersPanel
            currentUserId={session.user.id}
            roles={roles}
            users={users}
          />
        ) : (
          <p className="text-sm text-shell-muted">Не удалось загрузить пользователей.</p>
        )
      ) : null}

      {activeTab === "analytics" ? (
        settings ? (
          <OrganizationSettingsForm settings={settings} />
        ) : (
          <p className="text-sm text-shell-muted">Не удалось загрузить настройки аналитики.</p>
        )
      ) : null}

      {activeTab === "integrations" ? (
        integrations ? (
          <SettingsIntegrationsPanel integrations={integrations} />
        ) : (
          <p className="text-sm text-shell-muted">Не удалось загрузить статусы интеграций.</p>
        )
      ) : null}

      {activeTab === "modules" ? (
        modules ? (
          <OrganizationModulesForm modules={modules} />
        ) : (
          <p className="text-sm text-shell-muted">Не удалось загрузить модули организации.</p>
        )
      ) : null}
    </div>
  );
}
