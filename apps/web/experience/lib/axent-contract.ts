import type { UIMessage } from "ai";
import type { CompositionPlan } from "./governance";
export type AxentMessage = UIMessage<
  { revision: string },
  { composition: CompositionPlan },
  { compose: { input: { intent: string }; output: CompositionPlan } }
>;
