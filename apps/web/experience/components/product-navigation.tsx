"use client";
import { ArrowLeft, ArrowRight, Home } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { IconButton } from "./ui";
export function ProductNavigation({
  onBack,
  onForward,
  onHome,
  canBack = true,
  canForward = true,
}: {
  onBack: () => void;
  onForward: () => void;
  onHome: () => void;
  canBack?: boolean;
  canForward?: boolean;
}) {
  const { t } = useLocale();
  return (
    <>
      <IconButton
        label={t("Atrás", "Back")}
        onClick={onBack}
        disabled={!canBack}
      >
        <ArrowLeft size={17} />
      </IconButton>
      <IconButton
        label={t("Adelante", "Forward")}
        onClick={onForward}
        disabled={!canForward}
      >
        <ArrowRight size={17} />
      </IconButton>
      <IconButton label={t("Panorama", "Panorama")} onClick={onHome}>
        <Home size={17} />
      </IconButton>
    </>
  );
}
