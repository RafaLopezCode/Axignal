import type { Nature, Translate } from "./observatory";

export function natureLabel(nature: Nature, t: Translate): string {
  switch (nature) {
    case "OBSERVED":
      return t("Observado", "Observed");
    case "DECLARED":
      return t("Declarado", "Declared");
    case "POTENTIAL":
      return t("Potencial", "Potential");
    case "UNKNOWN":
      return t("Desconocido", "Unknown");
    case "STRENGTH":
      return t("Se entiende bien", "Understood well");
    case "CLARIFY":
      return t("Conviene aclarar", "Worth clarifying");
    case "UNRESOLVED":
      return t("Sin conclusión", "No conclusion");
  }
}
