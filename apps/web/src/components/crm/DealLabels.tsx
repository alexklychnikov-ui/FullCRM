"use client";

import { useI18n } from "@/lib/i18n";
import { resolveDealStatus, resolveStageName } from "@/lib/i18n/labels";

type DealStageLabelProps = {
  stageName: string | null | undefined;
  empty?: string;
};

export function DealStageLabel({ stageName, empty = "—" }: DealStageLabelProps) {
  const { t } = useI18n();

  if (!stageName) {
    return <>{empty}</>;
  }

  return <>{resolveStageName(stageName, t)}</>;
}

type DealStatusLabelProps = {
  status: string | null | undefined;
  empty?: string;
};

export function DealStatusLabel({ status, empty = "—" }: DealStatusLabelProps) {
  const { t } = useI18n();

  if (!status) {
    return <>{empty}</>;
  }

  return <>{resolveDealStatus(status, t)}</>;
}
