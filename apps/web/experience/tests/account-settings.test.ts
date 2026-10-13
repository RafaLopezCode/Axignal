import test,{afterEach} from "node:test";
import assert from "node:assert/strict";
import { subscriberAccount } from "../lib/subscriber-server";
import { accountProfileSchema, profileCommandSchema, approvedPortalUrl } from "../lib/account-contracts";
import { translate } from "../lib/copy-catalog";
import { readFileSync } from "node:fs";
const savedFetch=globalThis.fetch, savedRuntime=process.env.AXIGNAL_RUNTIME_ORIGIN,savedOrigin=process.env.AXIGNAL_EXPERIENCE_ORIGIN;
afterEach(()=>{globalThis.fetch=savedFetch;if(savedRuntime===undefined)delete process.env.AXIGNAL_RUNTIME_ORIGIN;else process.env.AXIGNAL_RUNTIME_ORIGIN=savedRuntime;if(savedOrigin===undefined)delete process.env.AXIGNAL_EXPERIENCE_ORIGIN;else process.env.AXIGNAL_EXPERIENCE_ORIGIN=savedOrigin;});
const token="a".repeat(48);
function request(body:unknown,origin="https://axignal.test") {return new Request("https://axignal.test/api/subscriber/profile",{method:"POST",headers:{host:"axignal.test",origin,cookie:`__Host-axignal-subscriber=${token}`,"content-type":"application/json"},body:JSON.stringify(body)});}
test("profile commands cannot select another owner or inject arbitrary fields",()=>{
 assert.equal(profileCommandSchema.safeParse({action:"locale",locale:"es",version:0,principalId:"other"}).success,false);
 assert.equal(profileCommandSchema.safeParse({action:"avatar",image:"https://attacker.test/avatar.svg",version:0}).success,false);
 assert.equal(accountProfileSchema.safeParse({state:"success",locale:"es",version:1,avatar:"data:image/svg+xml;base64,AAA="}).success,false);
});
test("profile proxy is same-origin and only forwards bounded typed preferences with the session",async()=>{
 process.env.AXIGNAL_RUNTIME_ORIGIN="http://127.0.0.1:18181";process.env.AXIGNAL_EXPERIENCE_ORIGIN="https://axignal.test";
 let called=0;globalThis.fetch=async(url,init)=>{called++;assert.equal(new URL(String(url)).pathname,"/subscriber/profile");assert.equal(new Headers(init?.headers).get("authorization"),`Bearer ${token}`);assert.deepEqual(JSON.parse(String(init?.body)),{action:"locale",locale:"es",version:0});return Response.json({state:"success",locale:"es",version:1,avatar:null});};
 assert.equal((await subscriberAccount(request({action:"locale",locale:"es",version:0},"https://other.test"),"profile",true)).status,403);
 assert.equal(called,0);
 const response=await subscriberAccount(request({action:"locale",locale:"es",version:0}),"profile",true);assert.equal(response.status,200);assert.equal(response.headers.get("cache-control"),"no-store");assert.equal(called,1);
});
test("profile conflict stays a conflict and portal host is exact",async()=>{
 process.env.AXIGNAL_RUNTIME_ORIGIN="http://127.0.0.1:18181";process.env.AXIGNAL_EXPERIENCE_ORIGIN="https://axignal.test";
 globalThis.fetch=async()=>Response.json({code:"PROFILE_CHANGED"},{status:409});
 assert.equal((await subscriberAccount(request({action:"locale",locale:"es",version:0}),"profile",true)).status,409);
 assert.ok(approvedPortalUrl("https://billing.stripe.com/p/session/test"));
 for(const url of ["https://billing.stripe.com.attacker.test/","https://user:pass@billing.stripe.com/","javascript:alert(1)","https://billing.stripe.com/#secret"])assert.equal(approvedPortalUrl(url),false);
});
test("new subscriber controls and dismissal labels are translated in every locale",()=>{
 for(const key of ["Change avatar","Account language","Change payment method","View and download invoices","Cancel renewal","Dismiss notice","Account and connections","Inspect basis and limits","Open available evidence","Illustrative explanation of fictional data; without live research. "])
  for(const locale of ["de","pt","fr","it"] as const)assert.notEqual(translate("es",key,locale),key);
});
test("temporary operation notices expose a keyboard-accessible dismissal without undoing state",()=>{
 const notice=readFileSync(new URL("../components/dismissible-notice.tsx",import.meta.url),"utf8");
 const observatory=readFileSync(new URL("../components/observatory.tsx",import.meta.url),"utf8");
 assert.match(notice,/aria-label=\{t\("Cerrar aviso","Dismiss notice"\)\}/);assert.match(notice,/event.key==="Escape"/);assert.match(observatory,/<DismissibleNotice key=\{props.message/);
});
