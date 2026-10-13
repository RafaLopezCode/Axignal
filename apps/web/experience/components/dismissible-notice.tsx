"use client";
import { useState } from "react";
import { X } from "lucide-react";
import { useLocale } from "@/lib/locale";
export function DismissibleNotice({children,className="obs-feedback",role="status"}:{children:React.ReactNode;className?:string;role?:"status"|"alert"}) {
  const [closed,setClosed]=useState(false); const {t}=useLocale();
  if(closed) return null;
  function close(){setClosed(true);document.getElementById("obs-main")?.focus({preventScroll:true});}
  return <div className={`${className} obs-dismissible`} role={role} aria-live={role==="alert"?"assertive":"polite"} onKeyDown={event=>{if(event.key==="Escape"){event.stopPropagation();close();}}}>
    <div>{children}</div><button type="button" className="obs-icon" onClick={close} aria-label={t("Cerrar aviso","Dismiss notice")}><X size={18} aria-hidden="true"/></button>
  </div>;
}
