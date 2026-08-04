import Link from "next/link";
import { cookies } from "next/headers";

import { CrmNav } from "@/components/crm/CrmNav";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCompanies } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function CompaniesPage() {
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

  return (
    <div>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Компании</h1>
          <p className="text-sm text-shell-muted">{companies.length} записей</p>
        </div>
        <Link
          className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white"
          href="/crm/companies/new"
        >
          Новая компания
        </Link>
      </div>
      <CrmNav active="companies" />
      <div className="overflow-hidden rounded-lg border border-shell-border">
        <table className="min-w-full text-sm">
          <thead className="bg-shell-panel text-left text-shell-muted">
            <tr>
              <th className="px-4 py-3">Название</th>
              <th className="px-4 py-3">Домен</th>
              <th className="px-4 py-3">Обновлено</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((company) => (
              <tr key={company.id} className="border-t border-shell-border">
                <td className="px-4 py-3">
                  <Link className="text-white hover:underline" href={`/crm/companies/${company.id}`}>
                    {company.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-shell-muted">{company.domain ?? "—"}</td>
                <td className="px-4 py-3 text-shell-muted">
                  {new Date(company.updated_at).toLocaleDateString("ru-RU")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
