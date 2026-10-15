import {operationalProjection,type OperationalProjection} from "./admin-projections";
import {ADMIN_RESPONSE_BYTE_LIMIT,readAdminText} from "./admin-json";
/** Migration adapter for the authorized AO-02 shell; HTML is never executed or forwarded. */
export async function readAdminRuntimePayload(response:Response):Promise<OperationalProjection> {
 const content=await readAdminText(response.body,ADMIN_RESPONSE_BYTE_LIMIT);
 const type=response.headers.get("content-type")?.split(";")[0].trim();
 let json=content;
 if(type==="text/html"){
  const parts=[...content.matchAll(/<div id="admin-bootstrap" hidden>([\s\S]*?)<\/div>/g)];
  if(parts.length!==1)throw new Error("invalid shell");
  json=parts[0][1].replaceAll("&lt;","<").replaceAll("&gt;",">").replaceAll("&amp;","&");
 }else if(type!=="application/json")throw new Error("unexpected response");
 return operationalProjection.parse(JSON.parse(json)) as OperationalProjection;
}
