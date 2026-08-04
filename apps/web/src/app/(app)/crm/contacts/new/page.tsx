import { cookies } from "next/headers";

import { NewContactForm } from "@/components/crm/NewContactForm";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCompanies } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function NewContactPage() {
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
  const companies = await fetchCompanies(cookieHeader);

  return <NewContactForm companies={companies} />;
}
