import {operationalProjection,type OperationalProjection} from "./admin-projections";
/** Migration adapter for the authorized AO-02 shell; HTML is never executed or forwarded. */
export async function readAdminRuntimePayload(response:Response):Promise<OperationalProjection> {
 const reader=response.body?.getReader();if(!reader)throw new Error("empty");
 let size=0;const chunks:Uint8Array[]=[];
 while(true){const item=await reader.read();if(item.done)break;size+=item.value.byteLength;if(size>1_048_576){await reader.cancel();throw new Error("limit");}chunks.push(item.value);}
 const content=Buffer.concat(chunks).toString("utf8");
 const type=response.headers.get("content-type")?.split(";")[0].trim();
 let json=content;
 if(type==="text/html"){
  const parts=[...content.matchAll(/<div id="admin-bootstrap" hidden>([\s\S]*?)<\/div>/g)];
  if(parts.length!==1)throw new Error("invalid shell");
  json=parts[0][1].replaceAll("&lt;","<").replaceAll("&gt;",">").replaceAll("&amp;","&");
 }else if(type!=="application/json")throw new Error("unexpected response");
 return operationalProjection.parse(JSON.parse(json)) as OperationalProjection;
}
