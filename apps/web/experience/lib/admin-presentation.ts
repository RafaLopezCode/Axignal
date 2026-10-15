import { label, scalar, type JsonValue } from "./admin-projections";
import type { Locale } from "./languages";

export type OperationalRecord = Record<string, JsonValue>;
export const isRecord = (value: JsonValue): value is OperationalRecord =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const locales: Locale[] = ["es", "en", "de", "pt", "fr", "it"];
export const operationalCopy: Record<string, readonly string[]> = {
  unit: ["Unidad de medida", "Measurement unit", "Maßeinheit", "Unidade de medida", "Unité de mesure", "Unità di misura"],
  metricId: ["Identificador del indicador", "Metric identifier", "Kennzahlkennung", "Identificador do indicador", "Identifiant de l’indicateur", "Identificatore dell’indicatore"],
  poolDisabled: ["El pool de marketing está desactivado. Su activación requiere autorización operativa.", "The marketing pool is disabled. Activation requires operational authorization.", "Der Marketing-Pool ist deaktiviert. Die Aktivierung erfordert eine betriebliche Freigabe.", "O pool de marketing está desativado. A ativação requer autorização operacional.", "Le pool marketing est désactivé. Son activation nécessite une autorisation opérationnelle.", "Il pool marketing è disattivato. L’attivazione richiede un’autorizzazione operativa."],
  source_projection_unavailable: ["No hay una proyección de origen disponible para este indicador.", "No source projection is available for this metric.", "Für diese Kennzahl ist keine Quellprojektion verfügbar.", "Não há uma projeção de origem disponível para este indicador.", "Aucune projection source n’est disponible pour cet indicateur.", "Non è disponibile una proiezione di origine per questo indicatore."],
  source_value_unavailable: ["La proyección de origen no contiene este valor.", "The source projection does not contain this value.", "Die Quellprojektion enthält diesen Wert nicht.", "A projeção de origem não contém este valor.", "La projection source ne contient pas cette valeur.", "La proiezione di origine non contiene questo valore."],
  methodology_version_unavailable: ["Falta la versión del método de cálculo.", "The calculation method version is missing.", "Die Version der Berechnungsmethode fehlt.", "Falta a versão do método de cálculo.", "La version de la méthode de calcul est absente.", "Manca la versione del metodo di calcolo."],
  currency_unavailable: ["Falta la moneda del importe de origen.", "The source amount has no currency.", "Die Währung des Quellbetrags fehlt.", "Falta a moeda do valor de origem.", "La devise du montant source est absente.", "Manca la valuta dell’importo di origine."],
  revokedSuccess: ["Revocación confirmada. El registro de acciones conserva el motivo.", "Revocation confirmed. The action history retains the reason.", "Widerruf bestätigt. Der Grund bleibt im Aktionsverlauf erhalten.", "Revogação confirmada. O histórico de ações mantém o motivo.", "Révocation confirmée. Le motif est conservé dans l’historique des actions.", "Revoca confermata. Il motivo rimane nella cronologia delle azioni."],
  ttlHelp: ["Entre 1 y 720 horas. El acceso piloto dura 60 días desde el canje.", "Between 1 and 720 hours. Pilot access lasts 60 days from redemption.", "Zwischen 1 und 720 Stunden. Der Pilotzugang gilt 60 Tage ab Einlösung.", "Entre 1 e 720 horas. O acesso piloto dura 60 dias após o resgate.", "Entre 1 et 720 heures. L’accès pilote dure 60 jours après utilisation.", "Tra 1 e 720 ore. L’accesso pilota dura 60 giorni dal riscatto."],
  reasonHelp: ["Al menos 8 caracteres. Se conserva en el registro de acciones.", "At least 8 characters. Retained in the action history.", "Mindestens 8 Zeichen. Wird im Aktionsverlauf gespeichert.", "Pelo menos 8 caracteres. Mantido no histórico de ações.", "Au moins 8 caractères. Conservé dans l’historique des actions.", "Almeno 8 caratteri. Conservato nella cronologia delle azioni."],
  sourceRecordTypes: ["Tipos de registro de origen", "Source record types", "Quelldatensatztypen", "Tipos de registo de origem", "Types d’enregistrements sources", "Tipi di record di origine"],
  requiredScope: ["Permiso requerido", "Required permission", "Erforderliche Berechtigung", "Permissão necessária", "Autorisation requise", "Permesso richiesto"],
  billedMinor: ["Facturado", "Billed", "In Rechnung gestellt", "Faturado", "Facturé", "Fatturato"],
  paidMinor: ["Pagado", "Paid", "Bezahlt", "Pago", "Payé", "Pagato"],
  refundedMinor: ["Reembolsado", "Refunded", "Erstattet", "Reembolsado", "Remboursé", "Rimborsato"],
  creditNoteMinor: ["Abonos", "Credit notes", "Gutschriften", "Notas de crédito", "Avoirs", "Note di credito"],
  processorFeeMinor: ["Comisiones de pago", "Payment fees", "Zahlungsgebühren", "Taxas de pagamento", "Frais de paiement", "Commissioni di pagamento"],
  settledGrossMinor: ["Liquidación bruta", "Gross settlement", "Bruttoabrechnung", "Liquidação bruta", "Règlement brut", "Liquidazione lorda"],
  settledNetMinor: ["Liquidación neta", "Net settlement", "Nettoabrechnung", "Liquidação líquida", "Règlement net", "Liquidazione netta"],
  accountedMinor: ["Contabilizado", "Accounted", "Verbucht", "Contabilizado", "Comptabilisé", "Contabilizzato"],
  infrastructureCostMinor: ["Coste de infraestructura", "Infrastructure cost", "Infrastrukturkosten", "Custo de infraestrutura", "Coût d’infrastructure", "Costo infrastruttura"],
  businessExpenseMinor: ["Gastos de AXIGNAL", "AXIGNAL expenses", "AXIGNAL-Ausgaben", "Despesas da AXIGNAL", "Dépenses AXIGNAL", "Spese AXIGNAL"],
  errorCount: ["Errores registrados", "Recorded errors", "Erfasste Fehler", "Erros registados", "Erreurs enregistrées", "Errori registrati"],
  quotaRemaining: ["Cuota restante", "Remaining quota", "Verbleibendes Kontingent", "Quota restante", "Quota restant", "Quota rimanente"],
  rateLimited: ["Límite de uso alcanzado", "Rate limited", "Nutzungslimit erreicht", "Limite de utilização atingido", "Limite d’utilisation atteinte", "Limite di utilizzo raggiunto"],
  reviewState: ["Revisión", "Review", "Prüfung", "Revisão", "Révision", "Revisione"],
  consentState: ["Consentimiento", "Consent", "Einwilligung", "Consentimento", "Consentement", "Consenso"],
  deliveryEligible: ["Entrega autorizada", "Delivery eligible", "Zustellberechtigt", "Entrega autorizada", "Livraison autorisée", "Consegna autorizzata"],
  requestedAt: ["Solicitud recibida", "Requested", "Angefragt", "Pedido recebido", "Demande reçue", "Richiesta ricevuta"],
  effectiveAt: ["Vigente desde", "Effective from", "Gültig ab", "Em vigor desde", "En vigueur depuis", "In vigore dal"],
  occurredAt: ["Fecha de la acción", "Action time", "Aktionszeitpunkt", "Data da ação", "Date de l’action", "Data dell’azione"],
  lastObservedAt: ["Última observación", "Last observation", "Letzte Beobachtung", "Última observação", "Dernière observation", "Ultima osservazione"],
  verified: ["Verificado", "Verified", "Verifiziert", "Verificado", "Vérifié", "Verificato"],
  pilot: ["Piloto", "Pilot", "Pilot", "Piloto", "Pilote", "Pilota"],
  staff_capacity: ["Capacidad interna", "Staff capacity", "Interne Kapazität", "Capacidade interna", "Capacité interne", "Capacità interna"],
  business: ["Actividad e ingresos", "Activity and revenue", "Aktivität und Umsatz", "Atividade e receitas", "Activité et revenus", "Attività e ricavi"],
  grossMinor: ["Importe bruto", "Gross amount", "Bruttobetrag", "Valor bruto", "Montant brut", "Importo lordo"],
  netMinor: ["Importe neto", "Net amount", "Nettobetrag", "Valor líquido", "Montant net", "Importo netto"],
  taxMinor: ["Impuestos", "Tax", "Steuern", "Impostos", "Taxes", "Imposte"],
  "execution-budget": ["Presupuesto de ejecución", "Execution budget", "Ausführungsbudget", "Orçamento de execução", "Budget d’exécution", "Budget di esecuzione"],
  "source-acquisition": ["Adquisición de fuentes", "Source acquisition", "Quellenbeschaffung", "Aquisição de fontes", "Acquisition de sources", "Acquisizione delle fonti"],
  "temporal-currentness": ["Vigencia temporal", "Temporal currentness", "Zeitliche Aktualität", "Atualidade temporal", "Actualité temporelle", "Attualità temporale"],
  retention: ["Conservación de datos", "Data retention", "Datenaufbewahrung", "Retenção de dados", "Conservation des données", "Conservazione dei dati"],
  "prime-routing": ["Selección de proveedores", "Provider routing", "Anbieterauswahl", "Seleção de fornecedores", "Sélection des fournisseurs", "Selezione dei fornitori"],
  "canonical-admission": ["Admisión de evidencia", "Evidence admission", "Evidenzzulassung", "Admissão de evidência", "Admission des preuves", "Ammissione delle prove"],
  alerting: ["Política de alertas", "Alert policy", "Alarmrichtlinie", "Política de alertas", "Politique d’alerte", "Politica degli avvisi"],
  unsupported_write_attempt: ["Escrituras no autorizadas", "Unauthorized writes", "Unbefugte Schreibversuche", "Escritas não autorizadas", "Écritures non autorisées", "Scritture non autorizzate"],
  stale_coverage: ["Cobertura desactualizada", "Stale coverage", "Veraltete Abdeckung", "Cobertura desatualizada", "Couverture périmée", "Copertura obsoleta"],
  source_failure: ["Fallos de fuentes", "Source failures", "Quellenfehler", "Falhas de fontes", "Échecs des sources", "Errori delle fonti"],
  provider_failure: ["Fallos de proveedores", "Provider failures", "Anbieterfehler", "Falhas de fornecedores", "Échecs des fournisseurs", "Errori dei fornitori"],
  cost_spike: ["Picos de coste", "Cost spikes", "Kostenspitzen", "Picos de custo", "Pics de coût", "Picchi di costo"],
  payment_failure: ["Fallos de pago", "Payment failures", "Zahlungsfehler", "Falhas de pagamento", "Échecs de paiement", "Errori di pagamento"],
  security_incident: ["Incidentes de seguridad", "Security incidents", "Sicherheitsvorfälle", "Incidentes de segurança", "Incidents de sécurité", "Incidenti di sicurezza"],
  governance_drift: ["Desviaciones de gobernanza", "Governance drift", "Governance-Abweichungen", "Desvios de governação", "Écarts de gouvernance", "Deviazioni di governance"],
  search: ["Buscar registros", "Search records", "Datensätze suchen", "Pesquisar registos", "Rechercher des enregistrements", "Cerca record"],
  all: ["Todos", "All", "Alle", "Todos", "Tous", "Tutti"],
  missing: ["Sin dato", "No data", "Keine Daten", "Sem dados", "Sans donnée", "Nessun dato"],
  available: ["Con datos", "With data", "Mit Daten", "Com dados", "Avec données", "Con dati"],
  clear: ["Limpiar búsqueda", "Clear search", "Suche löschen", "Limpar pesquisa", "Effacer la recherche", "Cancella ricerca"],
  noMatches: ["Ningún registro coincide con la búsqueda.", "No records match your search.", "Keine Datensätze entsprechen Ihrer Suche.", "Nenhum registo corresponde à pesquisa.", "Aucun enregistrement ne correspond à la recherche.", "Nessun record corrisponde alla ricerca."],
  previous: ["Anterior", "Previous", "Zurück", "Anterior", "Précédent", "Precedente"],
  next: ["Siguiente", "Next", "Weiter", "Seguinte", "Suivant", "Successivo"],
  shown: ["Mostrando", "Showing", "Angezeigt", "A mostrar", "Affichage", "Visualizzati"],
  of: ["de", "of", "von", "de", "sur", "di"],
  retry: ["Volver a intentar", "Try again", "Erneut versuchen", "Tentar novamente", "Réessayer", "Riprova"],
  readOnly: ["Consulta privada", "Private reading", "Private Ansicht", "Consulta privada", "Consultation privée", "Consultazione privata"],
  limited: ["Cobertura limitada", "Limited coverage", "Begrenzte Abdeckung", "Cobertura limitada", "Couverture limitée", "Copertura limitata"],
  noValues: ["No hay valores disponibles en esta proyección. Consulta las fuentes para conocer el límite.", "No values are available in this projection. Inspect the sources to understand the limitation.", "In dieser Projektion sind keine Werte verfügbar. Die Quellen erläutern die Grenzen.", "Não há valores disponíveis nesta projeção. Consulte as fontes para conhecer o limite.", "Aucune valeur disponible dans cette projection. Consultez les sources pour comprendre la limite.", "Nessun valore disponibile in questa proiezione. Consulta le fonti per comprenderne il limite."],
  updated: ["Lectura actualizada", "Reading refreshed", "Ansicht aktualisiert", "Leitura atualizada", "Lecture actualisée", "Lettura aggiornata"],
  identity: ["Referencia del registro", "Record reference", "Datensatzreferenz", "Referência do registo", "Référence du dossier", "Riferimento del record"],
  context: ["Contexto y condiciones", "Context and conditions", "Kontext und Bedingungen", "Contexto e condições", "Contexte et conditions", "Contesto e condizioni"],
  coverageNotes: ["Alcance de la lectura", "Reading scope", "Umfang der Ansicht", "Âmbito da leitura", "Périmètre de lecture", "Ambito della lettura"],
  sourceRecordIds: ["Registros de origen", "Source records", "Quelldatensätze", "Registos de origem", "Enregistrements sources", "Record di origine"],
  sourceLearningEventIds: ["Eventos de aprendizaje", "Learning events", "Lernereignisse", "Eventos de aprendizagem", "Événements d’apprentissage", "Eventi di apprendimento"],
  sourceAdminRecordIds: ["Registros operativos", "Operational records", "Betriebsdatensätze", "Registos operacionais", "Enregistrements opérationnels", "Record operativi"],
  sourceRefs: ["Referencias de origen", "Source references", "Quellenreferenzen", "Referências de origem", "Références sources", "Riferimenti di origine"],
  unknownReason: ["Motivo de la limitación", "Reason for limitation", "Grund der Einschränkung", "Motivo da limitação", "Motif de la limitation", "Motivo della limitazione"],
  sourceProjectionId: ["Proyección de origen", "Source projection", "Quellprojektion", "Projeção de origem", "Projection source", "Proiezione di origine"],
  methodologyVersion: ["Método de la fuente", "Source methodology", "Quellenmethodik", "Método da fonte", "Méthode de la source", "Metodo della fonte"],
  expectedMethodologyVersion: ["Método requerido", "Required methodology", "Erforderliche Methodik", "Método necessário", "Méthode requise", "Metodo richiesto"],
  purpose: ["Propósito", "Purpose", "Zweck", "Finalidade", "Finalité", "Scopo"],
  reason: ["Motivo", "Reason", "Grund", "Motivo", "Motif", "Motivo"],
  reference: ["Referencia", "Reference", "Referenz", "Referência", "Référence", "Riferimento"],
  environment: ["Entorno", "Environment", "Umgebung", "Ambiente", "Environnement", "Ambiente"],
  owner: ["Responsable", "Owner", "Verantwortlich", "Responsável", "Responsable", "Responsabile"],
  family: ["Familia", "Family", "Familie", "Família", "Famille", "Famiglia"],
  action: ["Acción", "Action", "Aktion", "Ação", "Action", "Azione"],
  outcome: ["Resultado", "Outcome", "Ergebnis", "Resultado", "Résultat", "Esito"],
  count: ["Registros", "Records", "Datensätze", "Registos", "Enregistrements", "Record"],
  changeCount: ["Cambios registrados", "Recorded changes", "Erfasste Änderungen", "Alterações registadas", "Changements enregistrés", "Modifiche registrate"],
  sampleSize: ["Tamaño de la muestra", "Sample size", "Stichprobengröße", "Dimensão da amostra", "Taille de l’échantillon", "Dimensione del campione"],
  questionServed: ["Pregunta que responde", "Question answered", "Beantwortete Frage", "Pergunta respondida", "Question traitée", "Domanda a cui risponde"],
  decisionServed: ["Decisión que informa", "Decision informed", "Unterstützte Entscheidung", "Decisão informada", "Décision éclairée", "Decisione supportata"],
  formulaOrCodingRule: ["Regla de cálculo", "Calculation rule", "Berechnungsregel", "Regra de cálculo", "Règle de calcul", "Regola di calcolo"],
  unsupportedCanonicalWriteTargetCount: ["Destinos de escritura no admitidos", "Unsupported write targets", "Nicht unterstützte Schreibziele", "Destinos de escrita não suportados", "Cibles d’écriture non prises en charge", "Destinazioni di scrittura non supportate"],
  deliveryEligibleCount: ["Solicitudes aptas para entrega", "Requests eligible for delivery", "Zustellfähige Anfragen", "Pedidos elegíveis para entrega", "Demandes éligibles à la livraison", "Richieste idonee alla consegna"],
  marketingEventCount: ["Eventos de adquisición", "Acquisition events", "Akquisitionsereignisse", "Eventos de aquisição", "Événements d’acquisition", "Eventi di acquisizione"],
  anonymousSessionCount: ["Sesiones anónimas", "Anonymous sessions", "Anonyme Sitzungen", "Sessões anónimas", "Sessions anonymes", "Sessioni anonime"],
  attributedRequestCount: ["Solicitudes atribuidas", "Attributed requests", "Zugeordnete Anfragen", "Pedidos atribuídos", "Demandes attribuées", "Richieste attribuite"],
  policyChanges: ["Historial de políticas", "Policy history", "Richtlinienverlauf", "Histórico de políticas", "Historique des politiques", "Cronologia delle politiche"],
  totals: ["Importes por moneda", "Amounts by currency", "Beträge nach Währung", "Valores por moeda", "Montants par devise", "Importi per valuta"],
  webhooks: ["Recepción de eventos", "Event reception", "Ereignisempfang", "Receção de eventos", "Réception des événements", "Ricezione degli eventi"],
  authEvents: ["Eventos de acceso", "Access events", "Zugriffsereignisse", "Eventos de acesso", "Événements d’accès", "Eventi di accesso"],
  received: ["Recibidos", "Received", "Empfangen", "Recebidos", "Reçus", "Ricevuti"],
  succeeded: ["Correctos", "Succeeded", "Erfolgreich", "Concluídos", "Réussis", "Riusciti"],
  retryPending: ["Reintentos pendientes", "Pending retries", "Ausstehende Wiederholungen", "Tentativas pendentes", "Nouvelles tentatives en attente", "Tentativi in sospeso"],
  deadLetter: ["Sin procesar", "Unprocessed", "Unverarbeitet", "Não processados", "Non traités", "Non elaborati"],
  rejected: ["Rechazados", "Rejected", "Abgelehnt", "Rejeitados", "Rejetés", "Rifiutati"],
  errors: ["Errores", "Errors", "Fehler", "Erros", "Erreurs", "Errori"],
};
export const text = (key: string, locale: Locale) =>
  operationalCopy[key]?.[locales.indexOf(locale)] ?? label(key, locale);
export const humanValue = (value: JsonValue, locale: Locale) =>
  typeof value === "string" && operationalCopy[value.toLowerCase()] ? text(value.toLowerCase(), locale) : scalar(value, locale);

export const isUnknown = (value: JsonValue | undefined) =>
  value === undefined || value === null || value === "UNKNOWN" || value === "NOT_AVAILABLE";

export function recordReference(record: OperationalRecord): string | null {
  for (const key of ["recordId", "xeedId", "policyId", "auditId", "decisionId", "integrationId", "measureId", "observationId", "obligationId", "issueId", "periodId", "endpointId", "requestId", "providerId"])
    if (typeof record[key] === "string" && record[key]) return record[key];
  return null;
}
export function recordTitle(record: OperationalRecord, locale: Locale, index: number): string {
  if (typeof record.metricId === "string") return label(record.metricId, locale);
  for (const key of ["displayName", "companyName", "label", "name", "purpose", "provider", "family", "alertClass", "modelCode", "action", "currency"])
    if (typeof record[key] === "string" && record[key]) return humanValue(record[key], locale);
  return recordReference(record) ?? `${label("records", locale)} ${index + 1}`;
}

export function formatValue(key: string, value: JsonValue, record: OperationalRecord, locale: Locale): string {
  if (isUnknown(value)) return label("unknown", locale);
  if (["dueAt", "periodStart", "periodEnd", "observedAt", "effectiveAt", "occurredAt", "lastVerifiedAt", "requestedAt", "lastObservedAt"].includes(key) && typeof value === "string" && Number.isFinite(Date.parse(value)))
    return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "Europe/Madrid" }).format(new Date(value));
  const number = typeof value === "number" ? value : typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value) ? Number(value) : NaN;
  if (Number.isFinite(number) && typeof record.currency === "string" && /^[A-Z]{3}$/.test(record.currency) && (key.endsWith("Minor") || (key === "value" && record.unit === "CURRENCY"))) {
    const formatter = new Intl.NumberFormat(locale, { style: "currency", currency: record.currency });
    const exponent = formatter.resolvedOptions().maximumFractionDigits ?? 2;
    return formatter.format(key.endsWith("Minor") ? number / 10 ** exponent : number);
  }
  return key === "value" && Number.isFinite(number) ? new Intl.NumberFormat(locale, { maximumFractionDigits: 6 }).format(number) : humanValue(value, locale);
}

/** Search only the visible record and its reference; arbitrary payload fields are excluded. */
export function matchesRecord(record: OperationalRecord, query: string, locale: Locale, index: number): boolean {
  const normalize = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase(locale);
  return normalize([recordTitle(record, locale, index), recordReference(record) ?? "", ...["state", "health", "completeness", "provider", "family", "outcome", "environment"].map(key => record[key] === undefined ? "" : humanValue(record[key], locale))].join(" ")).includes(normalize(query.trim()));
}
