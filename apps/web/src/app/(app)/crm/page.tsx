import Link from "next/link";

import { CrmNav } from "@/components/crm/CrmNav";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function CrmPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!hasModule(session, "crm")) {
    return <ModuleDisabledState />;
  }

  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold">CRM</h1>
      <p className="mb-6 text-sm text-shell-muted">
        Компании, контакты, сделки и воронка продаж.
      </p>
      <CrmNav active="companies" />
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          className="rounded-lg border border-shell-border bg-shell-panel p-5 transition hover:border-shell-accent/50"
          href="/crm/companies"
        >
          <h2 className="font-medium text-white">Компании</h2>
          <p className="mt-1 text-sm text-shell-muted">Список и карточки компаний</p>
        </Link>
        <Link
          className="rounded-lg border border-shell-border bg-shell-panel p-5 transition hover:border-shell-accent/50"
          href="/crm/contacts"
        >
          <h2 className="font-medium text-white">Контакты</h2>
          <p className="mt-1 text-sm text-shell-muted">Люди и связи с компаниями</p>
        </Link>
        <Link
          className="rounded-lg border border-shell-border bg-shell-panel p-5 transition hover:border-shell-accent/50"
          href="/crm/deals"
        >
          <h2 className="font-medium text-white">Сделки</h2>
          <p className="mt-1 text-sm text-shell-muted">Воронка, этапы и ответственные</p>
        </Link>
      </div>
    </div>
  );
}
