import type { ReactNode } from "react";

export function ModulePlaceholder({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-white">{title}</h1>
      {children ?? (
        <p className="text-sm text-shell-muted">
          Раздел будет доступен на следующих этапах MVP.
        </p>
      )}
    </div>
  );
}
