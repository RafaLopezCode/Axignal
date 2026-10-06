"""Autonomous, budgeted, fractal observation runtime.

Wakes once a day, decides deterministically what deserves observation, spends
a persistent daily budget on an explainable research frontier, lets evidence
age without fake fetches, expands only within family policy and stops. It is
operational control: it never calls a model and never writes AXIGLAND.
"""

from application.observation_runtime.acquirers import (
    PROCUREMENT_QUESTIONS,
    ProcurementAcquirer,
    PublicWebsiteAcquirer,
    procurement_acquirers,
)
from application.observation_runtime.budget import (
    BudgetDenial,
    BudgetScope,
    BudgetUsage,
    DailyObservationBudget,
)
from application.observation_runtime.digest import (
    DigestOpportunity,
    FamilyReading,
    ObservationDigest,
    observation_digest,
)
from application.observation_runtime.families import (
    FAMILY_POLICIES,
    FAMILY_POLICY_VERSION,
    LEAD_CAPABILITY,
    EntryPoint,
    FamilyObservationPolicy,
    FollowUpRule,
    LeadKind,
    ObservationFamily,
)
from application.observation_runtime.frontier import (
    LeadOutcome,
    LeadStatus,
    LeadTier,
    ResearchLead,
    explain,
    lead_id,
    lead_order,
)
from application.observation_runtime.ports import (
    AcquiredEvidence,
    Acquisition,
    AcquisitionPort,
    AcquisitionRequest,
    EvidenceState,
    LeadHint,
    LeaseLost,
    ObservationRuntimeStore,
    PendingRecompute,
    RecomputationPort,
    RecomputationRequest,
    RecomputeTrigger,
    StoredCandidate,
    TickClaim,
    XeedAttention,
)
from application.observation_runtime.tick import (
    TICK_POLICY_VERSION,
    ExecutedLead,
    TickReport,
    TickStatus,
    TickStopReason,
    run_daily_tick,
)

__all__ = [
    "FAMILY_POLICIES",
    "FAMILY_POLICY_VERSION",
    "LEAD_CAPABILITY",
    "PROCUREMENT_QUESTIONS",
    "TICK_POLICY_VERSION",
    "AcquiredEvidence",
    "Acquisition",
    "AcquisitionPort",
    "AcquisitionRequest",
    "BudgetDenial",
    "BudgetScope",
    "BudgetUsage",
    "DailyObservationBudget",
    "DigestOpportunity",
    "EntryPoint",
    "EvidenceState",
    "ExecutedLead",
    "FamilyObservationPolicy",
    "FamilyReading",
    "FollowUpRule",
    "LeadHint",
    "LeadKind",
    "LeadOutcome",
    "LeadStatus",
    "LeadTier",
    "LeaseLost",
    "ObservationDigest",
    "ObservationFamily",
    "ObservationRuntimeStore",
    "PendingRecompute",
    "ProcurementAcquirer",
    "PublicWebsiteAcquirer",
    "RecomputationPort",
    "RecomputationRequest",
    "RecomputeTrigger",
    "ResearchLead",
    "StoredCandidate",
    "TickClaim",
    "TickReport",
    "TickStatus",
    "TickStopReason",
    "XeedAttention",
    "explain",
    "lead_id",
    "lead_order",
    "observation_digest",
    "procurement_acquirers",
    "run_daily_tick",
]
