import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CommunicationComposer } from "@/components/communications/CommunicationComposer";
import { CommunicationTimeline } from "@/components/communications/CommunicationTimeline";
import { ContactDetailForm } from "@/components/crm/ContactDetailForm";
import { CrmNav } from "@/components/crm/CrmNav";
import { EventTimeline } from "@/components/crm/EventTimeline";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCommunicationsTimeline } from "@/lib/api/communications";
import { fetchCompanies, fetchContact, fetchEventLogs } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

type ContactDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ContactDetailPage({ params }: ContactDetailPageProps) {
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
    const [contact, companies, events, communications] = await Promise.all([
      fetchContact(id, cookieHeader),
      fetchCompanies(cookieHeader),
      fetchEventLogs({ entity_type: "contact", entity_id: id }, cookieHeader),
      hasModule(session, "communications")
        ? fetchCommunicationsTimeline({ contact_id: id }, cookieHeader)
        : Promise.resolve([]),
    ]);

    return (
      <div>
        <h1 className="mb-6 text-2xl font-semibold">{contact.full_name}</h1>
        <CrmNav active="contacts" />
        <ContactDetailForm companies={companies} contact={contact} />
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">События</h2>
          <EventTimeline events={events} />
        </section>
        {hasModule(session, "communications") ? (
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-medium">Коммуникации</h2>
            <CommunicationTimeline items={communications} />
            <CommunicationComposer
              companyId={contact.company_id}
              contactId={contact.id}
            />
          </section>
        ) : null}
      </div>
    );
  } catch {
    notFound();
  }
}
