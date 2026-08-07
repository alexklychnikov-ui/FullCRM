import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { DealAiAdvisoryPanel } from "@/components/ai/DealAiAdvisoryPanel";
import { CommunicationComposer } from "@/components/communications/CommunicationComposer";
import { CommunicationTimeline } from "@/components/communications/CommunicationTimeline";
import { CrmNav } from "@/components/crm/CrmNav";
import { DealDetailForm } from "@/components/crm/DealDetailForm";
import { EventTimeline } from "@/components/crm/EventTimeline";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchAiStatus } from "@/lib/api/ai";
import { fetchCommunicationsTimeline } from "@/lib/api/communications";
import {
  fetchAssignees,
  fetchCompanies,
  fetchContacts,
  fetchDeal,
  fetchEventLogs,
  fetchPipelines,
} from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

type DealDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function DealDetailPage({ params }: DealDetailPageProps) {
  const { id } = await params;
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!hasModule(session, "crm")) {
    return <ModuleDisabledState />;
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  try {
    const [deal, pipelines, companies, contacts, assignees, events, communications, aiStatus] = await Promise.all([
      fetchDeal(id, cookieHeader),
      fetchPipelines(cookieHeader),
      fetchCompanies(cookieHeader),
      fetchContacts(cookieHeader),
      fetchAssignees(cookieHeader),
      fetchEventLogs({ entity_type: "deal", entity_id: id }, cookieHeader),
      hasModule(session, "communications")
        ? fetchCommunicationsTimeline({ deal_id: id }, cookieHeader)
        : Promise.resolve([]),
      hasModule(session, "ai")
        ? fetchAiStatus(cookieHeader).catch(() => null)
        : Promise.resolve(null),
    ]);

    const pipeline = pipelines.find((item) => item.id === deal.pipeline_id);

    return (
      <div>
        <h1 className="mb-6 text-2xl font-semibold">{deal.title}</h1>
        <CrmNav active="deals" />
        <DealDetailForm
          assignees={assignees}
          companies={companies}
          contacts={contacts}
          deal={deal}
          pipelineStages={pipeline?.stages ?? []}
        />
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">События</h2>
          <EventTimeline events={events} />
        </section>
        {hasModule(session, "communications") ? (
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-medium">Коммуникации</h2>
            <CommunicationTimeline items={communications} />
            <CommunicationComposer
              companyId={deal.company_id}
              contactId={deal.contact_id}
              dealId={deal.id}
            />
          </section>
        ) : null}
        {hasModule(session, "ai") ? (
          <section className="mt-8">
            <DealAiAdvisoryPanel dealId={deal.id} initialStatus={aiStatus} />
          </section>
        ) : null}
      </div>
    );
  } catch {
    notFound();
  }
}
