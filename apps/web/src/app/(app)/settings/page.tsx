import { cookies } from "next/headers";

import { OrganizationSettingsForm } from "@/components/settings/OrganizationSettingsForm";
import { fetchOrganizationSettings } from "@/lib/api/organizations";
import { getServerSession } from "@/lib/auth/session";

export default async function SettingsPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!session.permissions.includes("admin.manage")) {
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Настройки</h1>
        <p className="text-sm text-shell-muted">Недостаточно прав для управления настройками организации.</p>
      </div>
    );
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  let settings = null;

  try {
    settings = await fetchOrganizationSettings(cookieHeader);
  } catch {
    settings = null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Настройки</h1>
        <p className="text-sm text-shell-muted">Параметры аналитики организации</p>
      </div>

      {settings ? (
        <OrganizationSettingsForm settings={settings} />
      ) : (
        <p className="text-sm text-shell-muted">Не удалось загрузить настройки.</p>
      )}
    </div>
  );
}
