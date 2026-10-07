export const legalIdentity = {
  controller: "Axignal SL",
  country: "España",
  publicEmail: "contacto@axignal.com",
} as const;

export const publicContactHref = `mailto:${legalIdentity.publicEmail}`;
