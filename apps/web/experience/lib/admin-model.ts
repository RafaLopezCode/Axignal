import type { Copy } from "./locale";
const c = (es: string, en: string): Copy => ({ es, en });
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
    name: c("Cuentas y suscripciones", "Accounts & subscriptions"),
    group: "operate",
    service: "SubscriberAccountService",
    question: c(
      "¿La atención asignada coincide con la suscripción?",
      "Does allocated attention match the subscription?",
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
];
export type AdminRecord = {
  id: string;
  domain: string;
  title: Copy;
  status: Copy;
  severity: "review" | "stable" | "unknown";
  detail: Copy;
  authority: "READ" | "WRITE" | "SENSITIVE" | "CRITICAL";
  action: Copy;
};
export const adminRecords: AdminRecord[] = [
  {
    id: "OPS-018",
    domain: "command",
    title: c("Una base requiere reevaluación", "A basis requires reassessment"),
    status: c("Revisión humana", "Human review"),
    severity: "review",
    detail: c(
      "Una fuente ilustrativa cambió de versión. Corresponde solicitar reevaluación a su servicio propietario; no editar el perfil económico.",
      "An illustrative source changed version. Reassessment belongs to its owning service; the economic profile must not be edited.",
    ),
    authority: "WRITE",
    action: c("Solicitar reevaluación", "Request reassessment"),
  },
  {
    id: "ACC-041",
    domain: "customers",
    title: c(
      "Alcance de observación de una cuenta",
      "An account’s observation scope",
    ),
    status: c("Ilustrativo", "Illustrative"),
    severity: "stable",
    detail: c(
      "La cuenta de ejemplo tiene un foco asignado. Esta vista es privada y no convierte al suscriptor en propietario de AXIGLAND.",
      "The example account has one allocated focus. This private view does not make the subscriber the owner of AXIGLAND.",
    ),
    authority: "SENSITIVE",
    action: c("Revisar asignación", "Review allocation"),
  },
  {
    id: "ACQ-009",
    domain: "acquisition",
    title: c("Origen de una solicitud", "Origin of a request"),
    status: c("Base limitada", "Limited basis"),
    severity: "unknown",
    detail: c(
      "La atribución no está completa. No inferimos campañas o conversiones que el read model no acredita.",
      "Attribution is incomplete. We do not infer campaigns or conversions unsupported by the read model.",
    ),
    authority: "READ",
    action: c("Revisar trazabilidad", "Review lineage"),
  },
  {
    id: "REV-027",
    domain: "revenue",
    title: c("Estado de una suscripción", "A subscription’s state"),
    status: c("Pendiente de conciliar", "Pending reconciliation"),
    severity: "review",
    detail: c(
      "El estado debe confirmarse en el servicio de facturación. Un webhook aislado no autoriza esta interfaz a cambiar condiciones.",
      "State must be confirmed in the billing service. An isolated webhook does not authorize this interface to change terms.",
    ),
    authority: "SENSITIVE",
    action: c("Revisar conciliación", "Review reconciliation"),
  },
  {
    id: "FOC-012",
    domain: "focus",
    title: c(
      "Atención persistente alrededor de Norte",
      "Persistent attention around Norte",
    ),
    status: c("Asignación ilustrativa", "Illustrative allocation"),
    severity: "stable",
    detail: c(
      "El foco dirige investigación y no duplica el mundo canónico. Su estado LIVE no representa una tarea que termine.",
      "The focus directs research and does not duplicate the canonical world. Its LIVE state is not a task that ends.",
    ),
    authority: "WRITE",
    action: c("Revisar alcance del foco", "Review focus scope"),
  },
  {
    id: "EVD-018",
    domain: "quality",
    title: c("Cambio de fuente y vigencia", "Source change and currentness"),
    status: c("Reevaluación pendiente", "Reassessment pending"),
    severity: "review",
    detail: c(
      "Reutilizar una conclusión requiere estado epistémico, provenance y vigencia. La admisión de evidencia pertenece al servicio canónico.",
      "Reusing a conclusion requires epistemic state, provenance and currentness. Evidence admission belongs to the canonical service.",
    ),
    authority: "CRITICAL",
    action: c("Revisar decisión de admisión", "Review admission decision"),
  },
  {
    id: "COG-005",
    domain: "brain",
    title: c("Investigación acotada", "Bounded research"),
    status: c("Sin proveedor en demo", "No provider in demo"),
    severity: "unknown",
    detail: c(
      "La explicación local es determinista. Una ejecución real debe pasar por cognition/router y la autoridad del proveedor configurado.",
      "The local explanation is deterministic. A real execution must pass through cognition/router and configured provider authority.",
    ),
    authority: "SENSITIVE",
    action: c("Revisar autoridad de ejecución", "Review execution authority"),
  },
  {
    id: "GOV-003",
    domain: "governance",
    title: c("Separación de identidades", "Identity separation"),
    status: c("Límite conservado", "Boundary preserved"),
    severity: "stable",
    detail: c(
      "AdminPrincipal y sesión privilegiada están separados del suscriptor. Un selector de rol en navegador nunca concede autorización.",
      "AdminPrincipal and privileged session are separate from subscriber identity. A browser role selector never grants authorization.",
    ),
    authority: "CRITICAL",
    action: c("Revisar política de acceso", "Review access policy"),
  },
  {
    id: "INT-008",
    domain: "integrations",
    title: c("Registro de conexión", "Connection registry"),
    status: c("No conectada", "Not connected"),
    severity: "unknown",
    detail: c(
      "Esta demo no usa credenciales ni obtiene datos externos. Cada integración necesita condiciones, alcance y autorización explícitos.",
      "This demo uses no credentials and retrieves no external data. Each integration needs explicit conditions, scope and authorization.",
    ),
    authority: "SENSITIVE",
    action: c("Revisar contrato de conexión", "Review connection contract"),
  },
  {
    id: "FIN-014",
    domain: "finance",
    title: c("Periodo operativo de ejemplo", "Example operational period"),
    status: c("Ilustrativo", "Illustrative"),
    severity: "stable",
    detail: c(
      "La información financiera pertenece a un read model privado. No es evidencia económica de las organizaciones observadas.",
      "Financial information belongs to a private read model. It is not economic evidence about observed organizations.",
    ),
    authority: "SENSITIVE",
    action: c("Revisar periodo", "Review period"),
  },
  {
    id: "ADV-006",
    domain: "advisor",
    title: c("Una propuesta para revisar", "A proposal to review"),
    status: c("No vinculante", "Non-binding"),
    severity: "review",
    detail: c(
      "La recomendación orienta una revisión humana; no se convierte en política ni conocimiento canónico de forma automática.",
      "The recommendation guides human review; it does not automatically become policy or canonical knowledge.",
    ),
    authority: "READ",
    action: c("Inspeccionar propuesta", "Inspect proposal"),
  },
  {
    id: "SYS-002",
    domain: "system",
    title: c("Proyección local disponible", "Local projection available"),
    status: c("Demo local", "Local demo"),
    severity: "stable",
    detail: c(
      "El estado confirma disponibilidad de esta aplicación local, sin atribuir salud o rendimiento a producción.",
      "The state confirms availability of this local app, without claiming production health or performance.",
    ),
    authority: "READ",
    action: c("Ver alcance del estado", "View state scope"),
  },
];
