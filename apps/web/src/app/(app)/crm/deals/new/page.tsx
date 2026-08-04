import { cookies } from "next/headers";

import { NewDealForm } from "@/components/crm/NewDealForm";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import {
  fetchAssignees,
  fetchCompanies,
  fetchContacts,
  fetchPipelines,
} from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function NewDealPage() {
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
  const [pipelines, companies, contacts, assignees] = await Promise.all([
    fetchPipelines(cookieHeader),
    fetchCompanies(cookieHeader),
    fetchContacts(cookieHeader),
    fetchAssignees(cookieHeader),
  ]);

  return (
    <NewDealForm
      assignees={assignees}
      companies={companies}
      contacts={contacts}
      defaultOwnerId={session.user.id}
      pipelines={pipelines}
    />
  );
}
