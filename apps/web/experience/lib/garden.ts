import type { Copy } from "./languages";
import type { Currentness, FactSource } from "./cognition/facts";
import type { Epistemic } from "./projection";

/**
 * The economic garden as people read it (spec 059): where a business works, where it
 * could grow, how distant changes can reach it, and what is still unknown. Every place
 * keeps its epistemic state, currentness and source; presentation never widens reach.
 */
export type GardenPlace = {
  code: string;
  label: Copy;
  state: Epistemic;
  currentness: Currentness;
  basis: Copy | null;
  source?: FactSource;
};
export type GardenExposure = { id: string; channel: Copy; path: Copy };
export type Garden = {
  operating: GardenPlace[];
  expansion: GardenPlace[];
  unknown: GardenPlace[];
  exposure: GardenExposure[];
};
