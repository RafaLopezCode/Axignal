import type { Copy } from "./languages";
import type { FactSource } from "./cognition/facts";
import type { Garden, GardenPlace } from "./garden";
import type { RuntimeEconomicGarden } from "./runtime-projection";

const c = (es: string, en: string): Copy => ({ es, en });
const same = (value: string): Copy => ({ es: value, en: value });

// How a distant change reaches a business through what it uses (spec 059 channels).
// Copy only: which channels apply is decided server-side from observed delivery modes.
const CHANNELS: Record<string, { channel: Copy; path: Copy }> = {
  PREMISES_ENERGY: {
    channel: c("Energía de sus instalaciones", "Energy for its premises"),
    path: c(
      "Atiende en sus propias instalaciones: el precio de la energía le afecta aunque cambie lejos.",
      "It serves customers at its own premises: energy prices affect it even when they change far away.",
    ),
  },
  FUEL_AND_TRAVEL: {
    channel: c("Combustible y desplazamientos", "Fuel and travel"),
    path: c(
      "Trabaja en casa del cliente: una subida del combustible le llega aunque ocurra lejos.",
      "It works at the customer's site: a fuel price rise reaches it even when it starts far away.",
    ),
  },
  FREIGHT_AND_CUSTOMS: {
    channel: c("Transporte y aduanas", "Freight and customs"),
    path: c(
      "Envía lo que vende: fletes y aduanas le afectan aunque el cambio ocurra lejos.",
      "It ships what it sells: freight and customs affect it even when the change happens far away.",
    ),
  },
  LOCAL_REGULATION: {
    channel: c("Normativa donde trabaja", "Rules where it works"),
    path: c(
      "Un cambio normativo le afecta solo si ocurre donde trabaja.",
      "A rule change affects it only where it works.",
    ),
  },
  DIGITAL_PLATFORM: {
    channel: c("Plataformas digitales", "Digital platforms"),
    path: c(
      "Presta su servicio en línea: un cambio en las plataformas que usa puede afectarle.",
      "It delivers online: a change in the platforms it relies on can affect it.",
    ),
  },
  SUPPLY_INPUTS: {
    channel: c("Suministros", "Supplies"),
    path: c(
      "Depende de proveedores que declara: lo que les ocurra puede llegarle.",
      "It depends on suppliers it names: what happens to them can reach it.",
    ),
  },
};

type RuntimePlace = RuntimeEconomicGarden["capabilities"][number]["operating"][number];

function source(place: RuntimePlace, asOf: string): FactSource {
  return {
    id: place.evidence,
    title: same(place.excerpt ? "“" + place.excerpt + "”" : place.source ?? place.evidence),
    observedAt: place.observedAt ?? asOf,
    instrument: same(place.source ?? place.evidence),
    limitation: c(
      "Lo que una organización dice de sí misma no demuestra actividad.",
      "What an organization says about itself does not prove activity.",
    ),
  };
}

function toPlaces(places: RuntimePlace[], asOf: string, expansion: boolean): GardenPlace[] {
  // One place per jurisdiction: a statement naming the activity beats a site-wide one,
  // and a current statement beats a stale one. Nothing is widened or invented.
  const best = new Map<string, RuntimePlace>();
  const rank = (p: RuntimePlace) => (p.stated ? 2 : 0) + (p.current ? 1 : 0);
  for (const place of places) {
    const known = best.get(place.geography);
    if (!known || rank(place) > rank(known)) best.set(place.geography, place);
  }
  return [...best.values()].map((place) => ({
    code: place.geography,
    label: same(place.label ?? place.geography),
    state: expansion || !place.stated || !place.current ? "POTENTIAL" : "OBSERVED",
    currentness: place.current ? "CURRENT" : "STALE",
    basis: expansion
      ? c("Señal de expansión propia: una oficina o una contratación.", "Own expansion signal: an office or a hire.")
      : place.stated
        ? c("Lo indica la propia organización para esta actividad.", "Stated by the organization for this activity.")
        : c("Lo indica para toda la organización, sin nombrar la actividad.", "Stated for the whole organization, without naming the activity."),
    source: source(place, asOf),
  }));
}

/** The persisted spec 059 garden as the shared reach view, or null when there is none. */
export function gardenFromRuntime(garden: RuntimeEconomicGarden | undefined, asOf: string): Garden | null {
  if (!garden || garden.capabilities.length === 0) return null;
  return {
    operating: toPlaces(garden.capabilities.flatMap((item) => item.operating), asOf, false),
    expansion: toPlaces(garden.capabilities.flatMap((item) => item.expansion), asOf, true),
    unknown: [],
    exposure: garden.exposureChannels.flatMap((id) => (CHANNELS[id] ? [{ id, ...CHANNELS[id] }] : [])),
  };
}
