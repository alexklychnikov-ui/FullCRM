import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CompanyDetailForm } from "@/components/crm/CompanyDetailForm";
import { CrmNav } from "@/components/crm/CrmNav";
import { EventTimeline } from "@/components/crm/EventTimeline";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCompany, fetchEventLogs } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

type CompanyDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function CompanyDetailPage({ params }: CompanyDetailPageProps) {
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
    const [company, events] = await Promise.all([
      fetchCompany(id, cookieHeader),
      fetchEventLogs({ entity_type: "company", entity_id: id }, cookieHeader),
    ]);

    return (
      <div>
        <h1 className="mb-6 text-2xl font-semibold">{company.name}</h1>
        <CrmNav active="companies" />
        <CompanyDetailForm company={company} />
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">События</h2>
          <EventTimeline events={events} />
        </section>
      </div>
    );
  } catch {
    notFound();
  }
}
