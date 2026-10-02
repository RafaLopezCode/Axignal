(() => {
  const $ = id => document.getElementById(id)
  const dialog = $('newsletterDialog')
  const form = $('newsletterForm')
  const submit = $('newsletterSubmit')
  const status = $('newsletterStatus')
  if (!dialog || !form || !submit || !status) return

  const copy = {
    en:{k:'FREE WEEKLY OBSERVATION',t:'See what changes outside your walls.',c:'Request a free weekly brief with up to three material public signals when the evidence supports them. This is not a free AXIGNAL plan.',company:'Company',domain:'Company domain',email:'Professional email',purpose:'What do you want AXIGNAL to observe?',request:'I have read the privacy notice and ask AXIGNAL to process this request.',consent:'If accepted, I consent to receive the AXIGNAL weekly observation newsletter by email.',send:'Request review',close:'Close',off:'Requests will open before public launch. No data has been sent.',sending:'Sending request…',ok:'Request received. AXIGNAL will review whether public evidence coverage is sufficient.',error:'The request could not be sent. Please try again later.'},
    es:{k:'OBSERVACIÓN SEMANAL GRATUITA',t:'Mira qué cambia fuera de tus paredes.',c:'Solicita un brief semanal gratuito con hasta tres señales públicas materiales cuando la evidencia las sostenga. No es un plan gratuito de AXIGNAL.',company:'Empresa',domain:'Dominio de la empresa',email:'Email profesional',purpose:'¿Qué quieres que observe AXIGNAL?',request:'He leído la política de privacidad y solicito que AXIGNAL trate esta petición.',consent:'Si se acepta, consiento recibir por email la newsletter semanal de observación de AXIGNAL.',send:'Solicitar revisión',close:'Cerrar',off:'Las solicitudes se abrirán antes del lanzamiento público. No se ha enviado ningún dato.',sending:'Enviando solicitud…',ok:'Solicitud recibida. AXIGNAL revisará si existe cobertura pública suficiente.',error:'No se pudo enviar la solicitud. Inténtalo más tarde.'},
    fr:{k:'OBSERVATION HEBDOMADAIRE GRATUITE',t:'Voyez ce qui change hors de vos murs.',c:'Demandez un brief hebdomadaire gratuit avec jusqu’à trois signaux publics matériels lorsque les preuves le permettent. Ce n’est pas une offre AXIGNAL gratuite.',company:'Entreprise',domain:'Domaine de l’entreprise',email:'Email professionnel',purpose:'Que voulez-vous qu’AXIGNAL observe ?',request:'J’ai lu la politique de confidentialité et je demande le traitement de cette demande.',consent:'Si elle est acceptée, je consens à recevoir la newsletter hebdomadaire d’observation AXIGNAL.',send:'Demander une revue',close:'Fermer',off:'Les demandes ouvriront avant le lancement public. Aucune donnée n’a été envoyée.',sending:'Envoi de la demande…',ok:'Demande reçue. AXIGNAL vérifiera si la couverture publique est suffisante.',error:'La demande n’a pas pu être envoyée. Réessayez plus tard.'},
  }
  Object.assign(copy,{
    de:{k:'KOSTENLOSE WÖCHENTLICHE BEOBACHTUNG',t:'Sehen Sie, was sich außerhalb Ihrer Mauern verändert.',c:'Fordern Sie einen kostenlosen wöchentlichen Brief mit bis zu drei wesentlichen öffentlichen Signalen an, sofern die Evidenz sie trägt. Dies ist kein kostenloser AXIGNAL-Tarif.',company:'Unternehmen',domain:'Unternehmensdomain',email:'Geschäftliche E-Mail',purpose:'Was soll AXIGNAL beobachten?',request:'Ich habe die Datenschutzhinweise gelesen und bitte AXIGNAL, diese Anfrage zu bearbeiten.',consent:'Bei Annahme willige ich ein, den wöchentlichen AXIGNAL-Beobachtungsnewsletter per E-Mail zu erhalten.',send:'Prüfung anfordern',close:'Schließen',off:'Anfragen werden vor dem öffentlichen Start geöffnet. Es wurden keine Daten gesendet.',sending:'Anfrage wird gesendet…',ok:'Anfrage eingegangen. AXIGNAL prüft, ob genügend öffentliche Evidenz vorliegt.',error:'Die Anfrage konnte nicht gesendet werden. Bitte später erneut versuchen.'},
    it:{k:'OSSERVAZIONE SETTIMANALE GRATUITA',t:'Scopri cosa cambia fuori dalle tue mura.',c:'Richiedi un brief settimanale gratuito con fino a tre segnali pubblici materiali quando le evidenze lo consentono. Non è un piano AXIGNAL gratuito.',company:'Azienda',domain:'Dominio aziendale',email:'Email professionale',purpose:'Cosa vuoi che AXIGNAL osservi?',request:'Ho letto l’informativa sulla privacy e chiedo ad AXIGNAL di trattare questa richiesta.',consent:'Se accettata, acconsento a ricevere via email la newsletter settimanale di osservazione AXIGNAL.',send:'Richiedi revisione',close:'Chiudi',off:'Le richieste apriranno prima del lancio pubblico. Nessun dato è stato inviato.',sending:'Invio richiesta…',ok:'Richiesta ricevuta. AXIGNAL verificherà se la copertura pubblica è sufficiente.',error:'Impossibile inviare la richiesta. Riprova più tardi.'},
    pt:{k:'OBSERVAÇÃO SEMANAL GRATUITA',t:'Veja o que muda fora das suas paredes.',c:'Solicite um brief semanal gratuito com até três sinais públicos materiais quando as evidências os sustentarem. Não é um plano gratuito da AXIGNAL.',company:'Empresa',domain:'Domínio da empresa',email:'Email profissional',purpose:'O que quer que a AXIGNAL observe?',request:'Li a política de privacidade e peço à AXIGNAL que trate este pedido.',consent:'Se for aceite, consinto receber por email a newsletter semanal de observação da AXIGNAL.',send:'Solicitar revisão',close:'Fechar',off:'Os pedidos abrirão antes do lançamento público. Nenhum dado foi enviado.',sending:'A enviar pedido…',ok:'Pedido recebido. A AXIGNAL verificará se existe cobertura pública suficiente.',error:'Não foi possível enviar o pedido. Tente mais tarde.'}
  })

  const privacyLabel = {
    en:'Privacy policy',
    es:'Política de privacidad',
    fr:'Politique de confidentialité',
    de:'Datenschutz',
    it:'Informativa sulla privacy',
    pt:'Política de privacidade'
  }

  let enabled = false
  let statusKnown = false

  function language(){
    const value=(document.documentElement.lang||'en').slice(0,2)
    return copy[value]?value:'en'
  }

  function applyCopy(){
    const c=copy[language()]
    $('newsletterDialogKicker').textContent=c.k
    $('newsletterDialogTitle').textContent=c.t
    $('newsletterDialogCopy').textContent=c.c
    $('newsletterCompanyLabel').textContent=c.company
    $('newsletterDomainLabel').textContent=c.domain
    $('newsletterEmailLabel').textContent=c.email
    $('newsletterPurposeLabel').textContent=c.purpose
    $('newsletterRequestNoticeLabel').textContent=c.request
    $('newsletterPrivacyLink').textContent=privacyLabel[language()]||privacyLabel.en
    $('newsletterConsentLabel').textContent=c.consent
    $('newsletterClose').textContent=c.close
    submit.textContent=c.send
    submit.disabled=!enabled
  }

  async function refreshStatus(){
    try{
      const response=await fetch('/api/weekly-brief/status',{headers:{Accept:'application/json'}})
      const data=await response.json()
      enabled=response.ok&&data.enabled===true
    }catch{
      enabled=false
    }
    statusKnown=true
    applyCopy()
    if(!enabled) status.textContent=copy[language()].off
  }

  async function openDialog(){
    applyCopy()
    status.textContent=''
    if(!statusKnown) await refreshStatus()
    else if(!enabled) status.textContent=copy[language()].off
    if(typeof dialog.showModal==='function') dialog.showModal()
  }

  $('newsletterClose').addEventListener('click',()=>dialog.close())
  dialog.addEventListener('click',event=>{
    if(event.target===dialog) dialog.close()
  })
  document.addEventListener('click',event=>{
    const trigger=event.target.closest('[data-newsletter-trigger]')
    if(trigger){
      event.preventDefault()
      void openDialog()
    }
  })

  form.addEventListener('submit',async event=>{
    event.preventDefault()
    const c=copy[language()]
    if(!enabled){
      status.textContent=c.off
      return
    }
    if(!form.reportValidity()) return
    submit.disabled=true
    status.textContent=c.sending
    const body={
      companyName:$('newsletterCompany').value.trim(),
      companyDomain:$('newsletterDomain').value.trim(),
      professionalEmail:$('newsletterEmail').value.trim(),
      purpose:$('newsletterPurpose').value.trim(),
      requestNoticeVersion:'weekly-brief-request-v1',
      requestProcessingAcknowledged:$('newsletterRequestNotice').checked,
      newsletterConsent:$('newsletterConsent').checked,
      newsletterNoticeVersion:$('newsletterConsent').checked?'weekly-newsletter-consent-v1':null
    }
    try{
      const response=await fetch('/api/weekly-brief/requests',{
        method:'POST',
        headers:{'Content-Type':'application/json','Accept':'application/json'},
        body:JSON.stringify(body)
      })
      if(!response.ok) throw new Error('request rejected')
      form.reset()
      status.textContent=c.ok
    }catch{
      status.textContent=c.error
    }finally{
      submit.disabled=!enabled
    }
  })

  applyCopy()
  void refreshStatus()
})()
