import { exampleInsights, type ExampleMoment } from "./landing-observatory";
import { evidence, signals } from "./projection";
import type { Copy } from "./languages";

/** Same existing fixture and state. Preserve full excerpts and instrument conditions in proof. */
export function labInsight(
  asOf: ExampleMoment,
  id: string,
  copy: (value: Copy) => string,
) {
  const insight = exampleInsights(asOf, copy).find((item) => item.id === id);
  if (!insight) return null;
  const signal = signals.find((item) => item.id === id)!;
  return {
    ...insight,
    sources: signal.evidenceIds.flatMap((ref) => {
      const source = evidence.find((item) => item.id === ref);
      if (!source || source.observedAt > asOf) return [];
      return [
        {
          url: null,
          label: copy(source.source),
          observedAt: source.observedAt,
          quote:
            copy(source.body) +
            (source.instrument ? " " + copy(source.instrument) : ""),
        },
      ];
    }),
  };
}
