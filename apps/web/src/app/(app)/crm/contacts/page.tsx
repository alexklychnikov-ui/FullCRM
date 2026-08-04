import Link from "next/link";
import { cookies } from "next/headers";

import { CrmNav } from "@/components/crm/CrmNav";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCompanies, fetchContacts } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function ContactsPage() {
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
  const [contacts, companies] = await Promise.all([
    fetchContacts(cookieHeader),
    fetchCompanies(cookieHeader),
  ]);
  const companyNames = new Map(companies.map((company) => [company.id, company.name]));

  return (
    <div>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Контакты</h1>
          <p className="text-sm text-shell-muted">{contacts.length} записей</p>
        </div>
        <Link
          className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white"
          href="/crm/contacts/new"
        >
          Новый контакт
        </Link>
      </div>
      <CrmNav active="contacts" />
      <div className="overflow-hidden rounded-lg border border-shell-border">
        <table className="min-w-full text-sm">
          <thead className="bg-shell-panel text-left text-shell-muted">
            <tr>
              <th className="px-4 py-3">Имя</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Компания</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((contact) => (
              <tr key={contact.id} className="border-t border-shell-border">
                <td className="px-4 py-3">
                  <Link className="text-white hover:underline" href={`/crm/contacts/${contact.id}`}>
                    {contact.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-shell-muted">{contact.email ?? "—"}</td>
                <td className="px-4 py-3 text-shell-muted">
                  {contact.company_id ? companyNames.get(contact.company_id) ?? "—" : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
