import { cookies } from "next/headers";

import { CommunicationTimeline } from "@/components/communications/CommunicationTimeline";
import { IntegrationStatusPanel } from "@/components/communications/IntegrationStatusPanel";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import {
  fetchCommunicationsTimeline,
  fetchIntegrationsStatus,
} from "@/lib/api/communications";
import { fetchContacts } from "@/lib/api/crm";
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

  const [integrations, contacts] = await Promise.all([
    fetchIntegrationsStatus(cookieHeader),
    fetchContacts(cookieHeader),
  ]);

  const contactId = contacts[0]?.id;
  const timeline = contactId
    ? await fetchCommunicationsTimeline({ contact_id: contactId }, cookieHeader)
    : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="mb-2 text-2xl font-semibold">Коммуникации</h1>
        <p className="text-sm text-shell-muted">
          Timeline MVP: Telegram polling при включённом флаге, Gmail/Calendar — stub boundary.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium">Интеграции</h2>
        <IntegrationStatusPanel integrations={integrations.integrations} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">
          Timeline{contactId ? ` · ${contacts[0]?.full_name ?? "контакт"}` : ""}
        </h2>
        <CommunicationTimeline items={timeline} />
      </section>
    </div>
  );
}
