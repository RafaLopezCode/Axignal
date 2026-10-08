import { publicChannelSubmit } from "@/lib/public-requests-server";
export const dynamic = "force-dynamic";
export const POST = (request: Request) => publicChannelSubmit(request, "contact");
