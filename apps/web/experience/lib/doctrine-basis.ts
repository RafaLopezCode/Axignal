export const basisSources = {
  "product-model": {
    title: {
      es: "Una arquitectura para comprender.",
      en: "An architecture for understanding.",
    },
    document: "AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md",
    language: "es",
    excerpts: [
      {
        section: "§1.1 · Lenguaje de producto humano",
        quote:
          "La arquitectura conserva un único AXIGLAND canónico, pero la interfaz pública no debe exigir al usuario aprender neologismos para comprender el producto.",
      },
      {
        section: "§1.1 · Organización y foco",
        quote:
          "Organización: sujeto económico que el usuario decide observar.\nFoco de observación / Observation Focus: asignación persistente de atención y cómputo alrededor de una Organización canónica.",
      },
      {
        section: "§1.1 · Panorama",
        quote:
          "Panorama: nombre humano de una proyección de AXIGLAND para el usuario. Panorama != AXIGLAND; no crea un segundo mundo ni una verdad privada.",
      },
      {
        section: "§3.1 · Un único mundo",
        quote:
          "Todos observan la misma realidad canónica desde perspectivas distintas.",
      },
      {
        section: "§4.3A · Autoridad de AXENT",
        quote: "AXENT HAS NO CANONICAL WRITE AUTHORITY",
        language: "en",
      },
      {
        section: "§55 · Evidencia y explicación",
        quote:
          "Explainable Basis does not itself authorize FAXT or canonical RELATIONSHIP. EvidenceAdmission remains the truth firewall.",
        language: "en",
      },
    ],
  },
  "human-first": {
    title: {
      es: "La profundidad puede ser sencilla.",
      en: "Depth can feel simple.",
    },
    document: "HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md",
    language: "en",
    excerpts: [
      {
        section: "North star",
        quote:
          "The sophistication of AXIGNAL must be experienced as simplicity, and that simplicity must never be purchased by hiding truth, uncertainty or evidence.",
      },
      {
        section: "Semantic depth and navigation",
        quote:
          "Depth is conceptual, not a mandatory wizard or four-screen funnel. A person may jump from a summary to evidence, evolution, comparison or AXENT. Preserve the selected object, relevant scope and a route back to its surrounding context.",
      },
      {
        section: "Hard interaction principles · Evidence on demand",
        quote:
          "A material output provides a direct path from human meaning through derivation and canonical references to permitted evidence. This is persisted provenance, not generated post-hoc storytelling.",
      },
      {
        section: "Independent output dimensions",
        quote:
          "UNKNOWN != FALSE, POTENTIAL != OBSERVED, and HISTORICAL != CURRENT. A human-friendly phrase may simplify vocabulary only when its mapping is deterministic and cannot change meaning.",
      },
    ],
  },
} as const;
export type BasisSource = keyof typeof basisSources;
