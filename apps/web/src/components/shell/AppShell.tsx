import type { ReactNode } from "react";

import { TopBar } from "@/components/shell/TopBar";
import { Sidebar } from "@/components/shell/Sidebar";
import type { AuthProfile } from "@/types/auth";

type AppShellProps = {
  session: AuthProfile;
  children: ReactNode;
};

export function AppShell({ session, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-shell-bg text-white">
      <Sidebar session={session} />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar session={session} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
