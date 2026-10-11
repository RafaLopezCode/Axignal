import type { Copy } from "./locale";
const c = (es: string, en: string): Copy => ({ es, en });

/**
 * The Admin's domains. A domain is listed for what the operator does there; whether this interface already
 * reads or writes through its owning service is declared in `connectedDomains`. Where it does not, the panel
 * says so and shows nothing: no sample record stands in for a service that is not connected.
 */
export const adminDomains = [
  {
    id: "command",
    name: c("Centro de atención", "Attention centre"),
    group: "observe",
    service: "OperationalReadModel",
    question: c(
      "¿Qué necesita una revisión humana?",
      "What needs human review?",
    ),
  },
  {
    id: "customers",
    name: c("Clientes y accesos", "Clients and access"),
    group: "operate",
    service: "PilotAccessService / CustomerOperations",
    question: c(
      "¿Quién tiene acceso y qué necesita para empezar?",
      "Who has access and what do they need to begin?",
    ),
  },
  {
    id: "acquisition",
    name: c("Adquisición", "Acquisition"),
    group: "operate",
    service: "AcquisitionReadModel",
    question: c(
      "¿Qué sabemos del origen de las solicitudes?",
      "What do we know about the origin of requests?",
    ),
  },
  {
    id: "revenue",
    name: c("Ingresos", "Revenue"),
    group: "operate",
    service: "BillingReadModel",
    question: c(
      "¿Qué estado está confirmado por el servicio de pagos?",
      "What state is confirmed by the payment service?",
    ),
  },
  {
    id: "focus",
    name: c("Focos de observación", "Observation focuses"),
    group: "observe",
    service: "ObservationAllocationService",
    question: c(
      "¿Dónde se asigna atención y con qué alcance?",
      "Where is attention allocated, and with what scope?",
    ),
  },
  {
    id: "quality",
    name: c("Calidad de AXIGLAND", "AXIGLAND quality"),
    group: "observe",
    service: "EvidenceAdmissionReadModel",
    question: c(
      "¿Qué necesita reevaluación sin editar verdad?",
      "What needs reassessment without editing truth?",
    ),
  },
  {
    id: "brain",
    name: c("AXENT y Brain", "AXENT & Brain"),
    group: "observe",
    service: "CognitionOperationalReadModel",
    question: c(
      "¿La investigación conserva sus límites y autoridad?",
      "Does research preserve its limits and authority?",
    ),
  },
  {
    id: "governance",
    name: c("Gobernanza", "Governance"),
    group: "govern",
    service: "GovernanceAuditService",
    question: c(
      "¿Podemos reconstruir la autoridad y el alcance?",
      "Can we reconstruct authority and scope?",
    ),
  },
  {
    id: "integrations",
    name: c("Integraciones", "Integrations"),
    group: "govern",
    service: "IntegrationRegistry",
    question: c(
      "¿Qué conexión está autorizada y bajo qué condiciones?",
      "Which connection is authorized, and under what conditions?",
    ),
  },
  {
    id: "finance",
    name: c("Finanzas y fiscalidad", "Finance & tax"),
    group: "operate",
    service: "FinanceOperationalReadModel",
    question: c(
      "¿La información está conciliada y en su periodo?",
      "Is information reconciled and in its period?",
    ),
  },
  {
    id: "advisor",
    name: c("Frontier Advisor", "Frontier Advisor"),
    group: "govern",
    service: "AdvisoryReadModel",
    question: c(
      "¿Qué recomendación requiere criterio y aprobación?",
      "Which recommendation requires judgment and approval?",
    ),
  },
  {
    id: "system",
    name: c("Sistema", "System"),
    group: "govern",
    service: "RuntimeOperationalReadModel",
    question: c(
      "¿La proyección disponible es actual y fiable?",
      "Is the available projection current and reliable?",
    ),
  },
] as const;

export type AdminDomain = (typeof adminDomains)[number];

/** Domains whose panel is backed by an authorized service in this interface. */
export const connectedDomains: ReadonlySet<string> = new Set(["customers"]);
