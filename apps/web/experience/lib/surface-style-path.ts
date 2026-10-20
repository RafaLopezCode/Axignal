/** Lab routes own their presentation; all other surfaces retain the legacy skin. */
export const isLandingLabPath = (path: string | null) =>
  /^\/(?:es\/|en\/|de\/|pt\/|fr\/|it\/)?landing-lab\/?$/.test(path ?? "");
