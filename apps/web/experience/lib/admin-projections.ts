import { z } from "zod";
import type { Locale } from "./languages";
export const operationalDomains = {
  command: "command-center", acquisition: "acquisition", revenue: "revenue",
  focus: "xeeds", quality: "axigland-quality", brain: "axent-brain",
  governance: "governance", integrations: "integrations", finance: "finance-fiscal",
  advisor: "frontier-advisor", system: "system",
} as const;
export type OperationalDomain = keyof typeof operationalDomains;
export const sectionNames = ["commandCenter", "xeedObservatory", "brainObservatory", "governance", "acquisition", "gsc", "integrations", "apiOperations", "financialDocuments", "accountingReconciliation", "fiscalCompliance", "taxOperations", "measurementRegistry"] as const;
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };
const jsonValue: z.ZodType<JsonValue> = z.lazy(() => z.union([z.string().max(8192), z.number().finite(), z.boolean(), z.null(), z.array(jsonValue).max(10000), z.record(z.string(), jsonValue)]));
export const operationalProjection = z.object({ mode: z.literal("ADMIN"), currentSlug: z.string(), ...Object.fromEntries(sectionNames.map(key => [key, z.record(z.string(), jsonValue).optional()])) });
export type OperationalProjection = {mode: "ADMIN"; currentSlug: string} & Partial<Record<(typeof sectionNames)[number], Record<string, JsonValue>>>;
export const domainSections: Record<OperationalDomain, readonly (typeof sectionNames)[number][]> = {
 command:["commandCenter"], revenue:["commandCenter"], system:["commandCenter"],
 focus:["xeedObservatory"], quality:["xeedObservatory"], brain:["brainObservatory"],
 governance:["governance"], acquisition:["acquisition","gsc"],
 integrations:["integrations","apiOperations"], finance:["financialDocuments","accountingReconciliation","fiscalCompliance","taxOperations"], advisor:["measurementRegistry"],
};
const languages: Locale[] = ["es", "en", "de", "pt", "fr", "it"];
export const labels: Record<string, readonly string[]> = {
  commandCenter: ["Lectura operativa", "Operational reading", "Betriebliche Übersicht", "Leitura operacional", "Lecture opérationnelle", "Lettura operativa"],
  xeedObservatory: ["Observación y memoria", "Observation and memory", "Beobachtung und Gedächtnis", "Observação e memória", "Observation et mémoire", "Osservazione e memoria"],
  brainObservatory: ["Investigación y proveedores", "Research and providers", "Forschung und Anbieter", "Investigação e fornecedores", "Recherche et fournisseurs", "Ricerca e fornitori"],
  governance: ["Políticas y auditoría", "Policies and audit", "Richtlinien und Prüfung", "Políticas e auditoria", "Politiques et audit", "Politiche e audit"],
  acquisition: ["Solicitudes y atribución", "Requests and attribution", "Anfragen und Zuordnung", "Pedidos e atribuição", "Demandes et attribution", "Richieste e attribuzione"],
  gsc: ["Analítica privada", "Private analytics", "Private Analysen", "Análise privada", "Analyse privée", "Analisi privata"],
  integrations: ["Conexiones autorizadas", "Authorized connections", "Autorisierte Verbindungen", "Ligações autorizadas", "Connexions autorisées", "Connessioni autorizzate"],
  apiOperations: ["Servicios y uso", "Services and usage", "Dienste und Nutzung", "Serviços e utilização", "Services et utilisation", "Servizi e utilizzo"],
  financialDocuments: ["Documentos financieros", "Financial documents", "Finanzdokumente", "Documentos financeiros", "Documents financiers", "Documenti finanziari"],
  accountingReconciliation: ["Conciliación", "Reconciliation", "Abstimmung", "Reconciliação", "Rapprochement", "Riconciliazione"],
  fiscalCompliance: ["Verificación fiscal", "Tax verification", "Steuerprüfung", "Verificação fiscal", "Vérification fiscale", "Verifica fiscale"],
  taxOperations: ["Obligaciones fiscales", "Tax obligations", "Steuerpflichten", "Obrigações fiscais", "Obligations fiscales", "Obblighi fiscali"],
  measurementRegistry: ["Definiciones y mediciones", "Definitions and measurements", "Definitionen und Messungen", "Definições e medições", "Définitions et mesures", "Definizioni e misurazioni"],
  loading: ["Consultando el servicio…", "Reading the service…", "Dienst wird abgefragt…", "A consultar o serviço…", "Consultation du service…", "Consultazione del servizio…"],
  unavailable: ["No se pudo consultar el servicio. Reintenta la lectura.", "Could not read the service. Retry the reading.", "Dienst konnte nicht abgefragt werden. Erneut versuchen.", "Não foi possível consultar o serviço. Tente novamente.", "Impossible de consulter le service. Réessayez.", "Impossibile consultare il servizio. Riprova."],
  denied: ["Tu sesión no autoriza esta sección.", "Your session does not authorize this section.", "Ihre Sitzung berechtigt nicht zu diesem Bereich.", "A sua sessão não autoriza esta secção.", "Votre session ne permet pas cette section.", "La tua sessione non autorizza questa sezione."],
  session: ["Necesitas una sesión Admin activa.", "An active Admin session is required.", "Eine aktive Admin-Sitzung ist erforderlich.", "É necessária uma sessão Admin ativa.", "Une session Admin active est requise.", "È necessaria una sessione Admin attiva."],
  empty: ["No hay registros en esta lectura.", "No records in this reading.", "Keine Datensätze in dieser Abfrage.", "Não há registos nesta leitura.", "Aucun enregistrement dans cette lecture.", "Nessun record in questa lettura."],
  unknown: ["Desconocido", "Unknown", "Unbekannt", "Desconhecido", "Inconnu", "Sconosciuto"],
  readAt: ["Lectura del servicio", "Service reading", "Dienstabfrage", "Leitura do serviço", "Lecture du service", "Lettura del servizio"],
  observedAt: ["Fecha de la proyección", "Projection time", "Projektionszeit", "Data da projeção", "Date de la projection", "Data della proiezione"],
  sources: ["Fuentes y límites", "Sources and limits", "Quellen und Grenzen", "Fontes e limites", "Sources et limites", "Fonti e limiti"],
  technical: ["Referencia técnica", "Technical reference", "Technische Referenz", "Referência técnica", "Référence technique", "Riferimento tecnico"],
  noSources: ["Sin referencias de fuente en esta lectura.", "No source references in this reading.", "Keine Quellenverweise in dieser Abfrage.", "Sem referências de fonte nesta leitura.", "Aucune référence de source dans cette lecture.", "Nessun riferimento alla fonte in questa lettura."],
  refresh: ["Actualizar", "Refresh", "Aktualisieren", "Atualizar", "Actualiser", "Aggiorna"],
  partial: ["Parcial", "Partial", "Teilweise", "Parcial", "Partiel", "Parziale"],
  complete: ["Completo", "Complete", "Vollständig", "Completo", "Complet", "Completo"],
  state: ["Estado", "State", "Status", "Estado", "État", "Stato"],
  value: ["Valor", "Value", "Wert", "Valor", "Valeur", "Valore"],
  total: ["Total", "Total", "Gesamt", "Total", "Total", "Totale"],
  active: ["Activo", "Active", "Aktiv", "Ativo", "Actif", "Attivo"],
  yes: ["Sí", "Yes", "Ja", "Sim", "Oui", "Sì"],
  no: ["No", "No", "Nein", "Não", "Non", "No"],
  metrics: ["Indicadores", "Metrics", "Kennzahlen", "Indicadores", "Indicateurs", "Indicatori"],
  xeeds: ["Focos de observación", "Observation focuses", "Beobachtungsfokusse", "Focos de observação", "Foyers d’observation", "Focus di osservazione"],
  axigland: ["AXIGLAND", "AXIGLAND", "AXIGLAND", "AXIGLAND", "AXIGLAND", "AXIGLAND"],
  control: ["Control de investigación", "Research control", "Forschungssteuerung", "Controlo de investigação", "Contrôle de recherche", "Controllo della ricerca"],
  policies: ["Políticas", "Policies", "Richtlinien", "Políticas", "Politiques", "Politiche"],
  alerts: ["Alertas", "Alerts", "Warnungen", "Alertas", "Alertes", "Avvisi"],
  auditRecords: ["Auditoría", "Audit", "Prüfung", "Auditoria", "Audit", "Audit"],
  requests: ["Solicitudes", "Requests", "Anfragen", "Pedidos", "Demandes", "Richieste"],
  records: ["Registros", "Records", "Datensätze", "Registos", "Enregistrements", "Record"],
  obligations: ["Obligaciones", "Obligations", "Pflichten", "Obrigações", "Obligations", "Obblighi"],
  issues: ["Incidencias", "Issues", "Probleme", "Incidências", "Anomalies", "Problemi"],
  periods: ["Periodos", "Periods", "Zeiträume", "Períodos", "Périodes", "Periodi"],
  definitions: ["Definiciones", "Definitions", "Definitionen", "Definições", "Définitions", "Definizioni"],
  readouts: ["Mediciones", "Measurements", "Messungen", "Medições", "Mesures", "Misurazioni"],
  endpoints: ["Puntos de conexión", "Endpoints", "Endpunkte", "Pontos de ligação", "Points de connexion", "Endpoint"],
  providerSlices: ["Uso por proveedor", "Usage by provider", "Nutzung je Anbieter", "Utilização por fornecedor", "Utilisation par fournisseur", "Utilizzo per fornitore"],
  completeness: ["Completitud", "Completeness", "Vollständigkeit", "Completude", "Complétude", "Completezza"],
  requestCount: ["Solicitudes recibidas", "Received requests", "Empfangene Anfragen", "Pedidos recebidos", "Demandes reçues", "Richieste ricevute"],
  acceptedCount: ["Solicitudes aceptadas", "Accepted requests", "Angenommene Anfragen", "Pedidos aceites", "Demandes acceptées", "Richieste accettate"],
  activeAccountCount: ["Cuentas activas", "Active accounts", "Aktive Konten", "Contas ativas", "Comptes actifs", "Account attivi"],
  eventCount: ["Eventos registrados", "Recorded events", "Erfasste Ereignisse", "Eventos registados", "Événements enregistrés", "Eventi registrati"],
  observationsAdded: ["Observaciones añadidas", "Added observations", "Hinzugefügte Beobachtungen", "Observações adicionadas", "Observations ajoutées", "Osservazioni aggiunte"],
  observationsReused: ["Observaciones reutilizadas", "Reused observations", "Wiederverwendete Beobachtungen", "Observações reutilizadas", "Observations réutilisées", "Osservazioni riutilizzate"],
  source_health: ["Estado de las fuentes", "Source health", "Quellenzustand", "Estado das fontes", "État des sources", "Stato delle fonti"],
  provider_health: ["Estado de los proveedores", "Provider health", "Anbieterzustand", "Estado dos fornecedores", "État des fournisseurs", "Stato dei fornitori"],
  system_health: ["Estado del sistema", "System health", "Systemzustand", "Estado do sistema", "État du système", "Stato del sistema"],
  mrr: ["Ingresos recurrentes mensuales", "Monthly recurring revenue", "Monatlich wiederkehrender Umsatz", "Receita recorrente mensal", "Revenus récurrents mensuels", "Ricavi ricorrenti mensili"],
  arr: ["Ingresos recurrentes anualizados", "Annualized recurring revenue", "Annualisierter wiederkehrender Umsatz", "Receita recorrente anualizada", "Revenus récurrents annualisés", "Ricavi ricorrenti annualizzati"],
  paying_accounts: ["Cuentas de pago", "Paying accounts", "Zahlende Konten", "Contas pagas", "Comptes payants", "Account paganti"],
  active_xeeds: ["Focos activos", "Active focuses", "Aktive Fokusse", "Focos ativos", "Foyers actifs", "Focus attivi"],
  evidence_coverage: ["Cobertura de evidencia", "Evidence coverage", "Evidenzabdeckung", "Cobertura de evidência", "Couverture des preuves", "Copertura delle evidenze"],
  currentness_quality: ["Vigencia de los datos", "Data currentness", "Datenaktualität", "Atualidade dos dados", "Actualité des données", "Attualità dei dati"],
  provenance_completeness: ["Trazabilidad", "Provenance", "Herkunftsnachweise", "Proveniência", "Provenance", "Provenienza"],
  open_incidents: ["Incidencias abiertas", "Open incidents", "Offene Vorfälle", "Incidências abertas", "Incidents ouverts", "Incidenti aperti"],
  cost_per_active_xeed_month: ["Coste mensual por foco activo", "Monthly cost per active focus", "Monatliche Kosten je aktivem Fokus", "Custo mensal por foco ativo", "Coût mensuel par foyer actif", "Costo mensile per focus attivo"],
  customer_product_activity: ["Actividad de las cuentas", "Account activity", "Kontoaktivität", "Atividade das contas", "Activité des comptes", "Attività degli account"],
  axigland_reuse_ratio: ["Reutilización en AXIGLAND", "AXIGLAND reuse", "AXIGLAND-Wiederverwendung", "Reutilização em AXIGLAND", "Réutilisation dans AXIGLAND", "Riutilizzo in AXIGLAND"],
  marginal_cost_per_xeed: ["Coste marginal por foco", "Marginal cost per focus", "Grenzkosten je Fokus", "Custo marginal por foco", "Coût marginal par foyer", "Costo marginale per focus"],
  "known": ["Conocido", "Known", "Bekannt", "Conhecido", "Connu", "Noto"],
  "current": ["Vigente", "Current", "Aktuell", "Atual", "À jour", "Attuale"],
  "stale": ["Desactualizado", "Stale", "Veraltet", "Desatualizado", "Périmé", "Obsoleto"],
  "healthy": ["Operativo", "Healthy", "Funktionsfähig", "Operacional", "Opérationnel", "Operativo"],
  "degraded": ["Degradado", "Degraded", "Beeinträchtigt", "Degradado", "Dégradé", "Degradato"],
  "failed": ["Fallido", "Failed", "Fehlgeschlagen", "Falhou", "Échec", "Fallito"],
  "lifecycleState": ["Ciclo de observación", "Observation lifecycle", "Beobachtungszyklus", "Ciclo de observação", "Cycle d’observation", "Ciclo di osservazione"],
  "currentnessState": ["Vigencia", "Currentness", "Aktualität", "Atualidade", "Actualité", "Attualità"],
  "provenanceState": ["Trazabilidad", "Provenance", "Herkunftsnachweise", "Proveniência", "Provenance", "Provenienza"],
  "contradictionState": ["Contradicciones", "Contradictions", "Widersprüche", "Contradições", "Contradictions", "Contraddizioni"],
  "observationCoverageState": ["Cobertura de observación", "Observation coverage", "Beobachtungsabdeckung", "Cobertura de observação", "Couverture d’observation", "Copertura di osservazione"],
  "identityResolutionState": ["Resolución de identidad", "Identity resolution", "Identitätsauflösung", "Resolução de identidade", "Résolution d’identité", "Risoluzione dell’identità"],
  "budgetState": ["Presupuesto", "Budget", "Budget", "Orçamento", "Budget", "Budget"],
  "routingState": ["Enrutamiento", "Routing", "Weiterleitung", "Encaminhamento", "Routage", "Instradamento"],
  "abstentionState": ["Abstención", "Abstention", "Enthaltung", "Abstenção", "Abstention", "Astensione"],
  "costCompleteness": ["Cobertura de costes", "Cost completeness", "Kostenabdeckung", "Cobertura de custos", "Couverture des coûts", "Copertura dei costi"],
  "learningEventCount": ["Eventos de aprendizaje", "Learning events", "Lernereignisse", "Eventos de aprendizagem", "Événements d’apprentissage", "Eventi di apprendimento"],
  "cognitiveEventCount": ["Eventos cognitivos", "Cognitive events", "Kognitive Ereignisse", "Eventos cognitivos", "Événements cognitifs", "Eventi cognitivi"],
  "failedEventCount": ["Eventos fallidos", "Failed events", "Fehlgeschlagene Ereignisse", "Eventos falhados", "Événements en échec", "Eventi falliti"],
  "averageLatencyMs": ["Latencia media (ms)", "Average latency (ms)", "Mittlere Latenz (ms)", "Latência média (ms)", "Latence moyenne (ms)", "Latenza media (ms)"],
  "latestRowCount": ["Filas en la última lectura", "Rows in latest reading", "Zeilen der letzten Abfrage", "Linhas na última leitura", "Lignes de la dernière lecture", "Righe nell’ultima lettura"],
  "consentedCount": ["Consentimientos registrados", "Recorded consents", "Erfasste Einwilligungen", "Consentimentos registados", "Consentements enregistrés", "Consensi registrati"],
  "coverageState": ["Cobertura", "Coverage", "Abdeckung", "Cobertura", "Couverture", "Copertura"],
  "health": ["Estado de la conexión", "Connection health", "Verbindungszustand", "Estado da ligação", "État de la connexion", "Stato della connessione"],
  "enabled": ["Habilitada", "Enabled", "Aktiviert", "Ativada", "Activée", "Abilitata"],
  "credentialConfigured": ["Credencial configurada", "Credential configured", "Zugangsdaten konfiguriert", "Credencial configurada", "Identifiant configuré", "Credenziale configurata"],
  "webhookConfigured": ["Webhook configurado", "Webhook configured", "Webhook konfiguriert", "Webhook configurado", "Webhook configuré", "Webhook configurato"],
  "credentialState": ["Estado de la credencial", "Credential state", "Status der Zugangsdaten", "Estado da credencial", "État de l’identifiant", "Stato della credenziale"],
  "provider": ["Proveedor", "Provider", "Anbieter", "Fornecedor", "Fournisseur", "Fornitore"],
  "grossMinor": ["Importe bruto (unidad menor)", "Gross amount (minor unit)", "Bruttobetrag (kleinste Einheit)", "Valor bruto (unidade menor)", "Montant brut (unité mineure)", "Importo lordo (unità minore)"],
  "netMinor": ["Importe neto (unidad menor)", "Net amount (minor unit)", "Nettobetrag (kleinste Einheit)", "Valor líquido (unidade menor)", "Montant net (unité mineure)", "Importo netto (unità minore)"],
  "taxMinor": ["Impuesto (unidad menor)", "Tax (minor unit)", "Steuer (kleinste Einheit)", "Imposto (unidade menor)", "Taxe (unité mineure)", "Imposta (unità minore)"],
  "currency": ["Moneda", "Currency", "Währung", "Moeda", "Devise", "Valuta"],
  "dueAt": ["Vencimiento", "Due date", "Fälligkeit", "Vencimento", "Échéance", "Scadenza"],
  "periodStart": ["Inicio del periodo", "Period start", "Periodenbeginn", "Início do período", "Début de période", "Inizio periodo"],
  "periodEnd": ["Fin del periodo", "Period end", "Periodenende", "Fim do período", "Fin de période", "Fine periodo"],
  "approvalEffective": ["Aprobación vigente", "Effective approval", "Wirksame Genehmigung", "Aprovação em vigor", "Approbation en vigueur", "Approvazione vigente"],
  "liveEnablementAllowed": ["Activación autorizada", "Live activation allowed", "Produktivaktivierung erlaubt", "Ativação autorizada", "Activation autorisée", "Attivazione autorizzata"],
  "complianceClaimAllowed": ["Cumplimiento acreditado", "Compliance claim allowed", "Konformitätsaussage erlaubt", "Conformidade comprovada", "Conformité attestée", "Conformità attestata"],
  "overdue": ["Fuera de plazo", "Overdue", "Überfällig", "Em atraso", "En retard", "Scaduto"],
  "notes": ["Los datos sin observación disponible se conservan como desconocidos.", "Values without available observations remain unknown.", "Werte ohne verfügbare Beobachtungen bleiben unbekannt.", "Os valores sem observações disponíveis permanecem desconhecidos.", "Les valeurs sans observation disponible restent inconnues.", "I valori senza osservazioni disponibili restano sconosciuti."],
  "no_provider": ["Sin proveedor", "No provider", "Kein Anbieter", "Sem fornecedor", "Aucun fournisseur", "Nessun fornitore"],
  "not_configured": ["Sin configurar", "Not configured", "Nicht konfiguriert", "Não configurado", "Non configuré", "Non configurato"],
  "not_applicable": ["No aplicable", "Not applicable", "Nicht zutreffend", "Não aplicável", "Non applicable", "Non applicabile"],
  "pending": ["Pendiente", "Pending", "Ausstehend", "Pendente", "En attente", "In attesa"],
  "open": ["Abierto", "Open", "Offen", "Aberto", "Ouvert", "Aperto"],
  "closed": ["Cerrado", "Closed", "Geschlossen", "Fechado", "Fermé", "Chiuso"],
  "completed": ["Completado", "Completed", "Abgeschlossen", "Concluído", "Terminé", "Completato"],
  "disabled": ["Desactivado", "Disabled", "Deaktiviert", "Desativado", "Désactivé", "Disabilitato"],
  "revoked": ["Revocado", "Revoked", "Widerrufen", "Revogado", "Révoqué", "Revocato"],
  "expired": ["Caducado", "Expired", "Abgelaufen", "Expirado", "Expiré", "Scaduto"],
  "confirmed": ["Confirmado", "Confirmed", "Bestätigt", "Confirmado", "Confirmé", "Confermato"],
  "valid": ["Válido", "Valid", "Gültig", "Válido", "Valide", "Valido"],
  "invalid": ["Inválido", "Invalid", "Ungültig", "Inválido", "Invalide", "Non valido"],
  "unresolved": ["Sin resolver", "Unresolved", "Ungeklärt", "Não resolvido", "Non résolu", "Non risolto"],
  critical_alerts: ["Alertas críticas", "Critical alerts", "Kritische Warnungen", "Alertas críticos", "Alertes critiques", "Avvisi critici"],
};
export function label(key: string, locale: Locale): string { return (labels[key] ?? labels.technical)[languages.indexOf(locale)]; }
export function scalar(value: JsonValue, locale: Locale): string {
  if (value === null || value === "UNKNOWN" || value === "NOT_AVAILABLE") return label("unknown", locale);
  if (typeof value === "boolean") return label(value ? "yes" : "no", locale);
  if (typeof value === "number") return new Intl.NumberFormat(locale).format(value);
  if (typeof value==="string" && Object.hasOwn(labels,value.toLowerCase())) return label(String(value).toLowerCase(), locale);
  return String(value);
}
export const visibleFields = new Set(["completeness", "state", "value", "requestCount", "acceptedCount", "eventCount", "observationsAdded", "observationsReused", "activeAccountCount", "lifecycleState","currentnessState","provenanceState","contradictionState","observationCoverageState","identityResolutionState","budgetState","routingState","abstentionState","costCompleteness","learningEventCount","cognitiveEventCount","failedEventCount","averageLatencyMs","latestRowCount","consentedCount","coverageState","health","enabled","credentialConfigured","webhookConfigured","credentialState","provider","grossMinor","netMinor","taxMinor","currency","dueAt","periodStart","periodEnd","approvalEffective","liveEnablementAllowed","complianceClaimAllowed","overdue"]);
export const collections = new Set(["metrics", "xeeds", "axigland", "control", "policies", "alerts", "auditRecords", "requests", "records", "obligations", "issues", "periods", "definitions", "readouts", "endpoints", "integrations", "providerSlices"]);

export async function readOperationalProjection(domain: OperationalDomain, signal: AbortSignal, fetcher: typeof fetch = fetch): Promise<OperationalProjection> {
 const response=await fetcher("/api/admin/projections/"+domain,{cache:"no-store",signal});
 if(!response.ok)throw new Error(response.status===401?"session":response.status===403?"denied":"unavailable");
 const data=operationalProjection.parse(await response.json()) as OperationalProjection;
 if(data.currentSlug!==operationalDomains[domain]||domainSections[domain].some(key=>!data[key]))throw new Error("unavailable");
 return data;
}
