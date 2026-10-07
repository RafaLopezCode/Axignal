import { z } from "zod";

const address = z.union([z.literal(""), z.email().max(254)]);
export const pilotAccountsCommand = z.object({
  a: address,
  b: address,
  expectedRevision: z.number().int().nonnegative(),
}).strict().refine(value => !value.a || value.a.toLowerCase() !== value.b.toLowerCase());
export const pilotAccountsSnapshot = z.object({
  a: address,
  b: address,
  revision: z.number().int().nonnegative(),
  authorizedForTest: z.boolean(),
  savedBy: z.string().nullable(),
  savedAt: z.string().nullable(),
}).strict().refine(value => value.authorizedForTest === Boolean(value.a && value.b));
export type PilotAccountsSnapshot = z.infer<typeof pilotAccountsSnapshot>;
