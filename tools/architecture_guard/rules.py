"""Architecture Guard rules.

Each rule derives from the MASTER via the Engineering Constitution. See
``docs/governance/ARCHITECTURE_GUARD.md``.
"""

from __future__ import annotations

from typing import Final

DOMAIN_PACKAGE: Final[str] = "domain"
XIGNAL_PACKAGE: Final[str] = "domain.xignal"
ORGANIZATIONS_PACKAGE: Final[str] = "domain.organizations"
PROVIDER_PACKAGE: Final[str] = "cognition.providers"

#: Domain is the innermost layer; these imports are forbidden from domain code.
DOMAIN_FORBIDDEN_IMPORTS: Final[tuple[str, ...]] = (
    "pipeline",
    "cognition",
    "apps",
    "tools",
)

#: Third-party model-provider SDKs may only appear under cognition/providers.
PROVIDER_SDK_PREFIXES: Final[tuple[str, ...]] = (
    "openai",
    "anthropic",
    "google.generativeai",
    "google.genai",
    "google.cloud.aiplatform",
    "vertexai",
    "genai",
    "transformers",
    "litellm",
    "cohere",
    "mistralai",
    "ollama",
    "huggingface_hub",
    "replicate",
    "together",
    "groq",
    "deepseek",
    "boto3",
)

#: CRM / workflow / sponsored truth drift must never enter the core layers.
FORBIDDEN_MODULE_SEGMENTS: Final[frozenset[str]] = frozenset(
    {
        "crm",
        "workflow",
        "workflow_engine",
        "sponsored",
        "pay_to_rank",
        "advertising",
    }
)

#: Modules that may create canonical state.
CANONICAL_WRITER_MODULES: Final[tuple[str, ...]] = (
    "domain.evidence.admission",
    "domain.faxt.model",
    "domain.relationships.model",
    "domain.organizations.model",
)

#: Projection / view packages. They read canonical state; they never write it.
PROJECTION_PACKAGES: Final[tuple[str, ...]] = (
    "domain.pathx",
    "domain.inxight",
    "domain.knowledge_frontier",
)

#: Layers scanned for forbidden drifting package names.
CORE_LAYERS: Final[tuple[str, ...]] = ("domain", "pipeline", "cognition")
