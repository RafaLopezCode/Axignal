"use client";
import { useLocale } from "@/lib/locale";

/** Inventory reflects the authorized projection, never a guessed plan allowance. */
export function RuntimeOrganizations({ name, internal, onReturn }: {
  name: string;
  internal: boolean;
  onReturn: () => void;
}) {
  const { t } = useLocale();
  return <div className="runtime-organizations">
    <p>{t("Estas son las organizaciones disponibles en tu contexto actual.", "These are the organizations available in your current context.")}</p>
    <button className="organization-switch" onClick={onReturn}>
      <strong>{name}</strong>
      <span>{t("Volver a la observación", "Return to observation")}</span>
    </button>
    <section aria-labelledby="add-organization-heading">
      <h3 id="add-organization-heading">{t("Añadir otra organización", "Add another organization")}</h3>
      <p id="organization-availability">{t("Todavía no disponible: el servicio actual solo permite observar AXIGNAL. No puede añadir ni guardar otros focos de observación.", "Not available yet: the current service only supports observing AXIGNAL. It cannot add or save other observation focuses.")}</p>
      <button className="button secondary" disabled aria-describedby="organization-availability">{t("Añadir organización", "Add organization")}</button>
      <p>{internal
        ? t("Customer Zero es uso interno del Admin, sin checkout ni pago. Añadir otros focos requiere autorización interna del servicio, con las mismas reglas de evidencia.", "Customer Zero is internal Admin use, without checkout or payment. Adding other focuses requires internal service authorization, with the same evidence rules.")
        : t("Este contexto no informa del plan ni de su capacidad disponible. No se puede deducir tu límite a partir de la organización visible.", "This context does not report your plan or its available capacity. Your limit cannot be inferred from the visible organization.")}</p>
    </section>
  </div>;
}
