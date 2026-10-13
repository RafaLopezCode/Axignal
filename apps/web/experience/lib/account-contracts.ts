import { z } from "zod";
export const accountProfileSchema = z.object({state:z.literal("success"),version:z.number().int().nonnegative(),locale:z.enum(["es","en","de","pt","fr","it"]).nullable(),avatar:z.string().max(174790).regex(/^data:image\/png;base64,[A-Za-z0-9+/]+=*$/).nullable()}).strict();
export type AccountProfile = z.infer<typeof accountProfileSchema>;
export const profileCommandSchema = z.discriminatedUnion("action",[
  z.object({action:z.literal("locale"),version:z.number().int().nonnegative(),locale:z.enum(["es","en","de","pt","fr","it"]).nullable()}).strict(),
  z.object({action:z.literal("avatar"),version:z.number().int().nonnegative(),image:z.string().min(1).max(174764).regex(/^[A-Za-z0-9+/]+=*$/)}).strict(),
  z.object({action:z.literal("remove_avatar"),version:z.number().int().nonnegative()}).strict(),
]);
export const billingManagementSchema = z.object({state:z.enum(["AVAILABLE","NO_SUBSCRIPTION","NOT_CONFIGURED","ACCESS_DENIED"]),canManage:z.boolean()}).strict().refine(value => value.canManage === (value.state === "AVAILABLE"));
export type BillingManagement = z.infer<typeof billingManagementSchema>;
export const billingManagementCommandSchema = z.object({action:z.enum(["payment_method","invoices","cancel"]),locale:z.enum(["es","en","de","pt","fr","it"])}).strict();
export function approvedPortalUrl(value: string): boolean {
  try {const url=new URL(value); return url.protocol === "https:" && url.hostname === "billing.stripe.com" && !url.username && !url.password && !url.port && !url.hash && value.length <= 2048;} catch {return false;}
}
export const billingPortalSchema = z.object({state:z.literal("success"),url:z.string().refine(approvedPortalUrl)}).strict();
