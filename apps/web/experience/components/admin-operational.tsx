"use client";
import {useEffect,useState} from "react";
import {useLocale} from "@/lib/locale";
import {collections,domainSections,label,readOperationalProjection,scalar,visibleFields,type JsonValue,type OperationalDomain,type OperationalProjection} from "@/lib/admin-projections";
import type {Locale} from "@/lib/languages";
const isObject=(value:JsonValue): value is Record<string,JsonValue> => value!==null && typeof value==="object" && !Array.isArray(value);
function Sources({record,locale}:{record:Record<string,JsonValue>;locale:Locale}) {
 const refs=["sourceRecordIds","sourceLearningEventIds","sourceAdminRecordIds","sourceRefs","sourceRecordTypes"].flatMap(key=>Array.isArray(record[key])?(record[key] as JsonValue[]).filter((v):v is string=>typeof v==="string"):[]);
 const codes=["unknownReason","sourceProjectionId","methodologyVersion","expectedMethodologyVersion","metricId","reason","recordId","sourceRef","sourceObjectRef","policyId","requiredScope","resultCode","unit"].flatMap(key=>typeof record[key]==="string"?[record[key] as string]:[]);
 const dates=["periodStart","periodEnd"].flatMap(key=>typeof record[key]==="string"&&Number.isFinite(Date.parse(record[key] as string))?[{key,value:record[key] as string}]:[]);
 return <details className="admin-source-details"><summary>{label("sources",locale)}</summary>
 {dates.map(({key,value})=><p key={key}>{label(key,locale)}: {new Intl.DateTimeFormat(locale,{dateStyle:"medium"}).format(new Date(value))}</p>)}
 {refs.length===0&&<p>{label("noSources",locale)}</p>}
 {[...new Set([...refs,...codes])].map(ref=><p key={ref}><span>{label("technical",locale)}: </span><code>{ref}</code></p>)}
 </details>;
}
export function Reading({record,locale,depth=0}:{record:Record<string,JsonValue>;locale:Locale;depth?:number}) {
 const metric=typeof record.metricId==="string";
 const fields=Object.entries(record).filter(([key,value])=>visibleFields.has(key)&&(value===null||typeof value!=="object")&&(!metric||key==="value"||key==="completeness"));
 const children=Object.entries(record).filter(([key,value])=>collections.has(key)&&value!==null&&typeof value==="object");
 return <>
 {fields.length>0&&<dl className="admin-reading-values">{fields.map(([key,value])=><div key={key}><dt>{label(key,locale)}</dt><dd>{["dueAt","periodStart","periodEnd"].includes(key)&&typeof value==="string"&&Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat(locale,{dateStyle:"medium"}).format(new Date(value)):scalar(value,locale)}{key==="value"&&typeof record.currency==="string"?" "+record.currency:""}</dd></div>)}</dl>}
 {depth<3&&children.map(([key,value])=><section className="admin-reading-group" key={key} aria-label={label(key,locale)}><h3>{label(key,locale)}</h3>
 {Array.isArray(value)?value.length===0?<p>{label("empty",locale)}</p>:<div className="admin-reading-grid">{value.map((item,index)=>isObject(item)?<article className="admin-reading-card" key={String(item.metricId??item.recordId??item.xeedId??index)}>
 <h4>{typeof item.metricId==="string"?label(item.metricId,locale):typeof item.displayName==="string"?item.displayName:typeof item.companyName==="string"?item.companyName:label("records",locale)+" "+(index+1)}</h4>
 <Reading record={item} locale={locale} depth={depth+1}/><Sources record={item} locale={locale}/>
 </article>:<p key={index}>{scalar(item,locale)}</p>)}</div>:isObject(value)?<Reading record={value} locale={locale} depth={depth+1}/>:null}
 </section>)}
 </>;
}
export function AdminOperationalPanel({domain}:{domain:OperationalDomain}) {
 const {locale}=useLocale(); const [retry,setRetry]=useState(0);
 const [state,setState]=useState<{domain:OperationalDomain;data:OperationalProjection|null;error:string|null;readAt:string|null}>({domain,data:null,error:null,readAt:null});
 useEffect(()=>{
  const controller=new AbortController(); setState({domain,data:null,error:null,readAt:null});
  void (async()=>{try {
   const data=await readOperationalProjection(domain,controller.signal);
   if(!controller.signal.aborted)setState({domain,data,error:null,readAt:new Date().toISOString()});
  }catch(error){if(!controller.signal.aborted)setState({domain,data:null,error:error instanceof Error&&["session","denied"].includes(error.message)?error.message:"unavailable",readAt:null});}})();
  return()=>controller.abort();
 },[domain,retry]);
 const current=state.domain===domain?state:null;
 const loading=!current||(!current.data&&!current.error);
 const date=(value:string)=>new Intl.DateTimeFormat(locale,{dateStyle:"medium",timeStyle:"short"}).format(new Date(value));
 return <div className="admin-operational" aria-busy={loading}>
 <p className="admin-reading-time">{label("notes",locale)}</p>
 <div className="admin-reading-toolbar"><button className="button secondary" disabled={loading} onClick={()=>setRetry(n=>n+1)}>{label("refresh",locale)}</button>
 {current?.readAt&&<p>{label("readAt",locale)} · <time dateTime={current.readAt}>{date(current.readAt)}</time></p>}</div>
 {loading&&<p role="status">{label("loading",locale)}</p>}
 {current?.error&&<p role="alert">{label(current.error,locale)}</p>}
 {current?.data&&domainSections[domain].map(key=>{const record=current.data![key]!; const timestamp=record.asOf??record.generatedAt;
 return <section className="admin-reading-section" key={key}><h2>{label(key,locale)}</h2>
 {typeof timestamp==="string"&&Number.isFinite(Date.parse(timestamp))&&<p className="admin-reading-time">{label("observedAt",locale)} · <time dateTime={timestamp}>{date(timestamp)}</time></p>}
 <Reading record={record} locale={locale}/><Sources record={record} locale={locale}/>
 </section>;})}
 </div>;
}
