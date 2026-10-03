import { preparedProviders } from "@/lib/public-contracts";
export function GET() {
  return Response.json(
    {
      providers: preparedProviders,
      identityScopes: ["openid", "profile", "email"],
      sessionCreated: false,
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
