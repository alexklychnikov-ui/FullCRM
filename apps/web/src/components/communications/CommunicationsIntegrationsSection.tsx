"use client";

import { IntegrationStatusPanel } from "@/components/communications/IntegrationStatusPanel";
import { useI18n } from "@/lib/i18n";
import type { IntegrationStatus } from "@/lib/api/communications";

type CommunicationsIntegrationsSectionProps = {
  integrations: IntegrationStatus[];
};

export function CommunicationsIntegrationsSection({
  integrations,
}: CommunicationsIntegrationsSectionProps) {
  const { t } = useI18n();

  return (
    <section>
      <h2 className="mb-3 text-lg font-medium">{t("comms.integrations.title")}</h2>
      <IntegrationStatusPanel integrations={integrations} />
    </section>
  );
}
