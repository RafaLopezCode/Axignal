import createCosmosAdapter from "./cosmos.js";
import createCytoscapeAdapter from "./cytoscape.js";
import createG6Adapter from "./g6.js";
import createSigmaAdapter from "./sigma.js";

export const ADAPTERS = {
  cytoscape: createCytoscapeAdapter,
  sigma: createSigmaAdapter,
  g6: createG6Adapter,
  cosmos: createCosmosAdapter,
};

export const ADOPTABLE = { cytoscape: true, sigma: true, g6: true, cosmos: false };
