"""Approved product documentation; never economic evidence or private memory."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any

from application.axent.grounded.corpus import fold

CATALOG: dict[str, Any] = json.loads(
    files("application.axent").joinpath("product-guide.json").read_text(encoding="utf-8")
)


def guide_topic(question: str) -> str | None:
    normalized = re.sub(r"[¿?¡!.,:;]+", "", fold(question)).strip()
    for topic, patterns in CATALOG["patterns"].items():
        if any(re.fullmatch(pattern, normalized) for pattern in patterns):
            return str(topic)
    return None


def product_guide_wire(
    question: str, locale: str, projection: dict[str, Any]
) -> dict[str, object] | None:
    topic = guide_topic(question)
    if topic is None:
        return None
    copy = CATALOG["locales"][locale]
    return {
        "organizationId": projection["organization"]["id"],
        "contextId": projection["context"]["id"],
        "signalIds": [],
        "intent": "known",
        "summary": copy[topic],
        "known": [],
        "openQuestions": [],
        "evidenceBasis": [],
        "researchPlan": [],
        "passages": [],
        "action": "unknown",
        "sourceRefs": [],
        "observedAt": [],
        "currentness": [],
        "productGuide": {
            "version": CATALOG["version"],
            "label": copy["label"],
            "topic": topic,
            "authority": CATALOG["authority"],
            "followUps": copy["followUps"],
        },
    }
