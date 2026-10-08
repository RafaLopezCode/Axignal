import { publicWeeklyBriefStatus } from "@/lib/public-requests-server";
export const dynamic = "force-dynamic";
export const GET = () => publicWeeklyBriefStatus();
