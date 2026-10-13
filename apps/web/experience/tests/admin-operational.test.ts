import test from "node:test";
import assert from "node:assert/strict";
import {createElement} from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {Reading} from "../components/admin-operational";
import {operationalDomains,domainSections,readOperationalProjection,labels,label,scalar,type OperationalDomain} from "../lib/admin-projections";
import {adminDomains,connectedDomains} from "../lib/admin-model";
import type {Locale} from "../lib/languages";
const locales:Locale[]=["es","en","de","pt","fr","it"];
test("every operational menu connects to a governed runtime domain",()=>{
 assert.deepEqual([...connectedDomains].sort(),adminDomains.map(d=>d.id).sort());
 assert.deepEqual(Object.keys(operationalDomains).sort(),adminDomains.filter(d=>d.id!=="customers").map(d=>d.id).sort());
});
for(const domain of Object.keys(operationalDomains) as OperationalDomain[]) test(domain+" reads only its projection and retains unknown",async()=>{
 const signal=new AbortController().signal;
 const body={mode:"ADMIN",currentSlug:operationalDomains[domain],...Object.fromEntries(domainSections[domain].map(key=>[key,{state:null}])),principalId:"private",sessionToken:"never forward"};
 const data=await readOperationalProjection(domain,signal,(async(url,init)=>{assert.equal(url,"/api/admin/projections/"+domain);assert.equal(init?.cache,"no-store");assert.equal(init?.signal,signal);return Response.json(body);}) as typeof fetch);
 assert.ok(domainSections[domain].every(key=>data[key]?.state===null));
 assert.equal("principalId" in data,false);assert.equal("sessionToken" in data,false);
});
test("denied, unavailable, wrong-domain and missing projection are rejected",async()=>{
 for(const [status,reason] of [[401,"session"],[403,"denied"],[503,"unavailable"]] as const) await assert.rejects(readOperationalProjection("command",new AbortController().signal,(async()=>Response.json({}, {status})) as typeof fetch),new RegExp(reason));
 for(const data of [{mode:"ADMIN",currentSlug:"revenue",commandCenter:{}},{mode:"ADMIN",currentSlug:"command-center"},{mode:"SUBSCRIBER",currentSlug:"command-center",commandCenter:{}}]) await assert.rejects(readOperationalProjection("command",new AbortController().signal,(async()=>Response.json(data)) as typeof fetch));
});
test("operational vocabulary has six complete translations",()=>{
 for(const [key,values]of Object.entries(labels)) {assert.equal(values.length,6,key);assert.ok(values.every(v=>v.length>0),key);for(const locale of locales) assert.ok(label(key,locale));}
 for(const locale of locales) {assert.notEqual(scalar(null,locale),"0");assert.equal(scalar(0,locale),"0");assert.equal(scalar("UNKNOWN",locale),label("unknown",locale));}
});
test("rendered readings distinguish unknown and zero and retain provenance without executing source text",()=>{
 for(const locale of locales){
 const html=renderToStaticMarkup(createElement(Reading,{locale,record:{metrics:[{metricId:"mrr",value:null,sourceRecordIds:[],unknownReason:"SOURCE_PROJECTION_UNAVAILABLE"},{metricId:"paying_accounts",value:0,sourceRecordIds:["billing:real-record"],reason:"<script>unsafe</script>"}]}}));
 assert.ok(html.includes(label("unknown",locale)));assert.ok(html.includes(">0<"));assert.ok(html.includes("billing:real-record"));assert.ok(html.includes(label("sources",locale)));assert.ok(!html.includes("<script>"));
 }
});


test("migration reads only the exact authorized shell bootstrap and never forwards HTML",async()=>{
 const {readAdminRuntimePayload}=await import("../lib/admin-runtime-response");
 const body={mode:"ADMIN",currentSlug:"command-center",commandCenter:{value:"<&>"}};
 const escaped=JSON.stringify(body).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
 const html='<html><div id="admin-bootstrap" hidden>'+escaped+'</div><script>unsafe()</script></html>';
 const read=await readAdminRuntimePayload(new Response(html,{headers:{"content-type":"text/html; charset=utf-8"}}));
 assert.equal(read.commandCenter?.value,"<&>");
 assert.equal("script" in read,false);
 for(const invalid of ['<html>not authorized</html>',html+html])await assert.rejects(readAdminRuntimePayload(new Response(invalid,{headers:{"content-type":"text/html"}})));
 await assert.rejects(readAdminRuntimePayload(new Response("x".repeat(1_048_577),{headers:{"content-type":"application/json"}})));
});
