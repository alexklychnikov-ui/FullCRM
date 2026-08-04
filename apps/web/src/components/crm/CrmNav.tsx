import Link from "next/link";

type CrmNavProps = {
  active: "companies" | "contacts" | "deals";
};

export function CrmNav({ active }: CrmNavProps) {
  const items = [
    { key: "companies" as const, href: "/crm/companies", label: "Компании" },
    { key: "contacts" as const, href: "/crm/contacts", label: "Контакты" },
    { key: "deals" as const, href: "/crm/deals", label: "Сделки" },
  ];

  return (
    <div className="mb-6 flex flex-wrap gap-2">
      {items.map((item) => (
        <Link
          key={item.key}
          className={`rounded-md px-4 py-2 text-sm transition ${
            active === item.key
              ? "bg-shell-accent/30 text-white"
              : "bg-shell-panel text-shell-muted hover:text-white"
          }`}
          href={item.href}
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}
