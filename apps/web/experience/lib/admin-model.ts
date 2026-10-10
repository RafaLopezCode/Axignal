import type { Copy } from "./locale";
const c = (es: string, en: string): Copy => ({ es, en });

/**
 * The Admin's functional domains. Customer Zero is the Admin's own AXIGNAL and is not listed here: it is the
 * default surface. Every domain below reads or writes through an authorized service; none carries sample data.
 */
export const adminDomains = [
  {
    id: "customers",
    name: c("Cuentas y capacidad", "Accounts & capacity"),
    service: "SubscriberAccountService",
    question: c(
      "¿Qué cuentas tienen capacidad concedida y cuánta?",
      "Which accounts hold granted capacity, and how much?",
    ),
  },
] as const;

export type AdminDomain = (typeof adminDomains)[number];
