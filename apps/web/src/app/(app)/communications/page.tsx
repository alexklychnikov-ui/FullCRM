import { cookies } from "next/headers";

import { IntegrationStatusPanel } from "@/components/communications/IntegrationStatusPanel";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchIntegrationsStatus } from "@/lib/api/communications";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function CommunicationsPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!hasModule(session, "communications")) {
    return <ModuleDisabledState />;
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  const integrations = await fetchIntegrationsStatus(cookieHeader);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="mb-2 text-2xl font-semibold">Коммуникации</h1>
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium">Интеграции</h2>
        <IntegrationStatusPanel integrations={integrations.integrations} />
      </section>
    </div>
  );
}
