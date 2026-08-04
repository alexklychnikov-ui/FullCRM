import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/LoginForm";
import { getServerSession } from "@/lib/auth/session";

type LoginPageProps = {
  searchParams: Promise<{ next?: string }>;
};

function sanitizeNextPath(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }

  return value;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const session = await getServerSession();

  if (session) {
    redirect("/dashboard");
  }

  const params = await searchParams;
  const nextPath = sanitizeNextPath(params.next);

  return (
    <div className="flex min-h-screen items-center justify-center bg-shell-bg px-4">
      <div className="w-full max-w-md rounded-xl border border-shell-border bg-shell-panel p-8 shadow-xl">
        <div className="mb-6 space-y-1">
          <h1 className="text-2xl font-semibold text-white">FullCRM</h1>
          <p className="text-sm text-shell-muted">Войдите в рабочую область организации</p>
        </div>
        <LoginForm nextPath={nextPath} />
      </div>
    </div>
  );
}
