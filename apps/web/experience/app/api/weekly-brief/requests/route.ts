import { publicWeeklyBriefSubmit } from "@/lib/public-requests-server";
export const dynamic = "force-dynamic";
export const POST = (request: Request) => publicWeeklyBriefSubmit(request);
