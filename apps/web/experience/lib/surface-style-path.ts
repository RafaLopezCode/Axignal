/** The approved public landing and its isolated preview share the lean landing skin. */
export const isLandingSurfacePath = (path: string | null) =>
  /^\/(?:es|en|de|pt|fr|it)?\/?$/.test(path ?? "") ||
  /^\/(?:es\/|en\/|de\/|pt\/|fr\/|it\/)?landing-lab\/?$/.test(path ?? "");
