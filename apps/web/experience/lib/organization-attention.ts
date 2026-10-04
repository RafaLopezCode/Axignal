import { z } from "zod";
const text = z.string().trim().min(1);
export const attentionCommandSchema = z.discriminatedUnion("action", [
  z.object({action:z.literal("add"),name:text.max(200),targetUri:text.max(2048)}).strict(),
  z.object({action:z.literal("select"),id:text.max(200)}).strict(),
  z.object({action:z.literal("reobserve"),id:text.max(200)}).strict(),
]);
export type AttentionCommand = z.infer<typeof attentionCommandSchema>;
export const organizationInventorySchema = z.object({
  accessMode:z.literal("INTERNAL_ADMIN"),canObserve:z.boolean(),selectedId:text.nullable(),
  organizations:z.array(z.object({id:text,requestedLabel:text,name:text.nullable(),
    organizationId:text.nullable(),targetUri:text,state:z.enum(["LIVE","IDENTITY_UNRESOLVED",
      "INSUFFICIENT_EVIDENCE","RUNTIME_FAILURE","RUN_INTERRUPTED","AUTHORIZATION_REVOKED"]),
    projectionContextId:text.nullable()})),
  available:z.array(z.object({name:text,targetUri:text})),
});
export type OrganizationInventory = z.infer<typeof organizationInventorySchema>;
