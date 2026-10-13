"use client";
import { useEffect, useRef, useState } from "react";
import { UserRound, CreditCard, FileText, ExternalLink } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { locales, type Locale } from "@/lib/languages";
import { billingManagementSchema, billingPortalSchema, type BillingManagement } from "@/lib/account-contracts";
import { DismissibleNotice } from "./dismissible-notice";

export function SubscriberAccountSettings() {
  const {t,locale,profile,profileLoading,profileSaving,profileError,reloadProfile,saveProfile,setLocale}=useLocale();
  const [billing,setBilling]=useState<BillingManagement|null>(null);
  const [billingBusy,setBillingBusy]=useState(false);
  const [billingError,setBillingError]=useState(false);
  const [notice,setNotice]=useState("");
  const [uploading,setUploading]=useState(false);
  const input=useRef<HTMLInputElement>(null);
  const billingController=useRef<AbortController|null>(null);
  async function reloadBilling(){
    billingController.current?.abort();const controller=new AbortController();billingController.current=controller;setBillingError(false);
    try {const response=await fetch("/api/subscriber/billing/management",{cache:"no-store",signal:controller.signal});
      if(!response.ok)throw new Error("BILLING_UNAVAILABLE");
      const value=billingManagementSchema.parse(await response.json());if(!controller.signal.aborted)setBilling(value);
    }catch {if(!controller.signal.aborted)setBillingError(true);}
  }
  useEffect(()=>{void reloadBilling();return ()=>billingController.current?.abort();},[]);
  async function upload(file:File|undefined){
    if(!file) return;setNotice("");setUploading(true);
    try {
      if(!["image/png","image/jpeg","image/webp"].includes(file.type)||file.size>5242880)throw new Error("IMAGE_REJECTED");
      const bitmap=await createImageBitmap(file);
      let encoded:string;
      try {
        if(Math.max(bitmap.width,bitmap.height)>8192||bitmap.width*bitmap.height>40000000)throw new Error("IMAGE_REJECTED");
        const canvas=document.createElement("canvas");canvas.width=128;canvas.height=128;
        const ctx=canvas.getContext("2d");if(!ctx)throw new Error("IMAGE_UNAVAILABLE");
        const side=Math.min(bitmap.width,bitmap.height);
        ctx.drawImage(bitmap,(bitmap.width-side)/2,(bitmap.height-side)/2,side,side,0,0,128,128);
        encoded=canvas.toDataURL("image/png").split(",")[1];
      } finally {bitmap.close();}
      if(!await saveProfile({action:"avatar",image:encoded}))throw new Error("NOT_SAVED");
      setNotice(t("Avatar guardado.","Avatar saved."));
    } catch {setNotice(t("No se pudo guardar el avatar. Usa una imagen PNG, JPEG o WebP de hasta 5 MB.","The avatar could not be saved. Use a PNG, JPEG or WebP image up to 5 MB."));}
    finally {setUploading(false);if(input.current)input.current.value="";}
  }
  async function remove(){setNotice("");if(await saveProfile({action:"remove_avatar"}))setNotice(t("Avatar eliminado.","Avatar removed."));}
  async function openBilling(action:"payment_method"|"invoices"|"cancel"){
    setBillingBusy(true);setBillingError(false);
    try {
      const response=await fetch("/api/subscriber/billing/management",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action,locale})});
      if(!response.ok)throw new Error("PORTAL_UNAVAILABLE");
      const result=billingPortalSchema.parse(await response.json());window.location.assign(result.url);
    }catch {setBillingError(true);setBillingBusy(false);}
  }
  const disabled=!profile||profileLoading||profileSaving||uploading;
  return <>
    <section className="obs-account-card" aria-labelledby="profile-title">
      <h2 id="profile-title">{t("Tu perfil privado","Your private profile")}</h2>
      <p className="obs-quiet">{t("Tu avatar e idioma se guardan en tu cuenta y no modifican ninguna organización.","Your avatar and language are saved in your account and do not change any organization.")}</p>
      <div className="obs-profile-avatar">{profile?.avatar?<img src={profile.avatar} width={64} height={64} alt={t("Tu avatar","Your avatar")}/>:<UserRound size={32} aria-hidden="true"/>}
        <div><button type="button" className="obs-button" disabled={disabled} onClick={()=>input.current?.click()}>{t("Cambiar avatar","Change avatar")}</button>
          <input ref={input} id="profile-avatar" type="file" hidden aria-hidden="true" tabIndex={-1} accept="image/png,image/jpeg,image/webp" disabled={disabled} onChange={event=>void upload(event.target.files?.[0])}/>
          <small>{t("PNG, JPEG o WebP · hasta 5 MB · recorte cuadrado","PNG, JPEG or WebP · up to 5 MB · square crop")}</small></div>
      </div>
      {profile?.avatar&&<button className="obs-link" disabled={disabled} onClick={()=>void remove()}>{t("Eliminar avatar","Remove avatar")}</button>}
      <label htmlFor="profile-locale">{t("Idioma de tu cuenta","Account language")}</label>
      <select id="profile-locale" value={profile?.locale??"auto"} disabled={disabled} onChange={event=>{setNotice("");if(event.target.value==="auto")void saveProfile({action:"locale",locale:null});else setLocale(event.target.value as Locale);}}>
        <option value="auto">{t("Usar el idioma del navegador","Use browser language")}</option>{locales.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
      {profileSaving||uploading?<p role="status">{t("Guardando…","Saving…")}</p>:profileLoading?<p role="status">{t("Leyendo tus preferencias…","Reading your preferences…")}</p>:profile&&!profileError&&<p className="obs-quiet">{t("Preferencias guardadas en tu cuenta.","Preferences saved in your account.")}</p>}
      {profileError&&<DismissibleNotice key="profile-error" role="alert"><p>{t("No se pudieron sincronizar tus preferencias. Vuelve a cargar antes de guardar.","Your preferences could not be synchronized. Reload before saving.")}</p><button className="obs-link" onClick={()=>void reloadProfile()}>{t("Volver a cargar","Reload")}</button></DismissibleNotice>}
      {notice&&<DismissibleNotice key={notice}><p>{notice}</p></DismissibleNotice>}
    </section>
    <section className="obs-account-card" aria-labelledby="billing-title">
      <h2 id="billing-title">{t("Suscripción y facturación","Subscription and billing")}</h2>
      <p>{t("Gestiona tus datos de pago y facturas en el portal seguro de Stripe.","Manage your payment details and invoices in Stripe’s secure portal.")}</p>
      <div className="obs-account-actions">
        <button className="obs-button" disabled={!billing?.canManage||billingBusy} onClick={()=>void openBilling("payment_method")}><CreditCard size={16} aria-hidden="true"/>{t("Cambiar método de pago","Change payment method")}<ExternalLink size={14} aria-hidden="true"/></button>
        <button className="obs-button" disabled={!billing?.canManage||billingBusy} onClick={()=>void openBilling("invoices")}><FileText size={16} aria-hidden="true"/>{t("Ver y descargar facturas","View and download invoices")}<ExternalLink size={14} aria-hidden="true"/></button>
        <button className="obs-link" disabled={!billing?.canManage||billingBusy} onClick={()=>void openBilling("cancel")}>{t("Cancelar renovación","Cancel renewal")}</button>
      </div>
      <p className="obs-quiet">{t("La cancelación se confirma en Stripe y se aplica al final del periodo contratado. Pausar una organización no cancela la suscripción.","Cancellation is confirmed in Stripe and takes effect at the end of the billing period. Pausing an organization does not cancel the subscription.")}</p>
      {billingBusy&&<p role="status">{t("Abriendo el portal seguro…","Opening the secure portal…")}</p>}
      {billing?.state==="NO_SUBSCRIPTION"&&<p>{t("No hay una suscripción de pago vinculada a esta cuenta.","No paid subscription is linked to this account.")}</p>}
      {billing?.state==="NOT_CONFIGURED"&&<p>{t("La gestión de facturación no está configurada en este entorno.","Billing management is not configured in this environment.")}</p>}
      {billing?.state==="ACCESS_DENIED"&&<p>{t("Solo la persona autorizada para facturar puede gestionar la suscripción.","Only the authorized billing owner can manage the subscription.")}</p>}
      {billingError&&<DismissibleNotice role="alert"><p>{t("No se pudo abrir o comprobar el portal. No se ha cambiado tu suscripción.","The portal could not be opened or checked. Your subscription has not been changed.")}</p><button className="obs-link" disabled={billingBusy} onClick={()=>void reloadBilling()}>{t("Volver a comprobar","Check again")}</button></DismissibleNotice>}
    </section>
  </>;
}
