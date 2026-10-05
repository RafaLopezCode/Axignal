"""Subscriber-runtime adapter for EB-08 Human Product & Production Proof.

This module maps the already-governed EconomicHumanOutput into the existing
subscriber RuntimeSignal/read-model shape. It does not create a new economic
model, truth authority, UI surface or canonical write path.
"""

from __future__ import annotations

from copy import deepcopy

from application.subscriber_projection.economic_output import EconomicHumanOutput
from domain.xignal import XignalEpistemicState


def _runtime_xignal_id(output: EconomicHumanOutput) -> str:
    suffix = output.output_id.split(":", 1)[-1]
    return f"xignal:economic:{suffix}"


def economic_output_runtime_signal(output: EconomicHumanOutput) -> dict[str, object]:
    """Compile one EconomicHumanOutput into the existing RuntimeSignal contract."""

    result = output.result
    evidence = tuple(datum for datum in result.basis.data)
    if not evidence:
        raise ValueError("economic runtime signal requires explainable evidence")

    source_refs = tuple(dict.fromkeys(item.source_ref for item in evidence))
    observed_at = max(item.observed_at for item in evidence)
    xignal_id = _runtime_xignal_id(output)

    steps: list[dict[str, object]] = [
        {
            "id": f"{xignal_id}:step:xignal",
            "kind": "XIGNAL",
            "label": output.one_sentence_meaning,
            "sourceRef": None,
            "observedAt": result.vector.evaluated_at.isoformat(),
            "currentness": output.temporal_state.value,
            "artifactVerified": None,
        }
    ]
    for index, item in enumerate(evidence, start=1):
        steps.append(
            {
                "id": f"{xignal_id}:step:evidence:{index:02d}",
                "kind": "OBSERVATION",
                "label": item.excerpt_or_summary,
                "sourceRef": item.source_ref,
                "observedAt": item.observed_at.isoformat(),
                "currentness": output.temporal_state.value,
                "artifactVerified": None,
            }
        )

    uncertainty_parts = (*output.unknowns, *output.contradictions)
    uncertainty = " · ".join(uncertainty_parts) if uncertainty_parts else result.basis.uncertainty
    if not uncertainty.strip():
        raise ValueError("economic runtime signal requires explicit uncertainty")

    return {
        "id": xignal_id,
        "nodeKind": "XIGNAL",
        "title": output.headline,
        "whyAttention": output.why_it_may_matter,
        "interpretation": output.one_sentence_meaning,
        "uncertainty": uncertainty,
        "epistemicState": result.interpretation.epistemic_state.value,
        "currentness": output.temporal_state.value,
        "observedAt": observed_at.isoformat(),
        "evidenceAccess": "AVAILABLE",
        "sourceRefs": list(source_refs),
        # Economic E2E observation ids are not automatically FR-30 ObservationMemory ids.
        # Evidence remains navigable through sourceRefs/evidenceNarrative until a governed
        # runtime persistence bridge explicitly binds those stores.
        "observationSupportRefs": [],
        "unknowns": list(output.unknowns),
        "evidenceNarrative": {
            "xignalId": xignal_id,
            "focusStepId": steps[0]["id"],
            "steps": steps,
        },
    }


def attach_economic_output(
    projection: dict[str, object],
    output: EconomicHumanOutput,
) -> dict[str, object]:
    """Return a copy of one subscriber projection with one economic Xignal attached."""

    result = output.result
    organization = projection.get("organization")
    if not isinstance(organization, dict):
        raise ValueError("subscriber projection requires organization context")
    organization_id = organization.get("id")
    if organization_id != result.candidate.subject.state.subject_id:
        raise ValueError("economic output subject must match subscriber organization context")

    attached = deepcopy(projection)
    nodes = attached.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("subscriber projection requires node collection")

    signal = economic_output_runtime_signal(output)
    signal_id = signal["id"]
    if any(isinstance(item, dict) and item.get("id") == signal_id for item in nodes):
        return attached
    nodes.append(signal)

    memberships = attached.setdefault("memberships", [])
    if isinstance(memberships, list):
        context = attached.get("context")
        if isinstance(context, dict) and isinstance(context.get("id"), str):
            memberships.append(
                {
                    "from": context["id"],
                    "to": signal_id,
                    "meaning": "Xeed observes Xignal",
                }
            )

    today = attached.get("today")
    if isinstance(today, dict):
        items = today.get("items")
        if isinstance(items, list):
            should_surface = (
                output.temporal_state.value == "CURRENT"
                and result.interpretation.epistemic_state
                in (XignalEpistemicState.POTENTIAL, XignalEpistemicState.UNKNOWN)
            )
            if should_surface:
                items.append(
                    {
                        "xignalId": signal_id,
                        "whatChanged": output.headline,
                        "whyItMatters": output.why_it_may_matter,
                        "observedAt": signal["observedAt"],
                        "showHowRef": signal_id,
                    }
                )
                today["disposition"] = "READY"

    attached["economicOutput"] = output.to_wire()
    return attached
