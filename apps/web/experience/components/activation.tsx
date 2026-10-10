"use client";

/**
 * Activation: the organization the person asked for is kept, and the screen says plainly what is missing and
 * what they can do. It offers only the ways in that exist for this account (an invitation, a subscription, or a
 * request for access); it never assumes capacity, never hides a price and never shows internal states.
 */
import { useState } from "react";
import Link from "next/link";
import { ArrowRight, CreditCard, KeyRound, Mail, RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { ADDITIONAL_ORGANIZATION_CENTS, FIRST_ORGANIZATION_CENTS, PUBLISHED_OFFER, capacityRoom, firstPurchaseTotal, inviteTokenFrom, type ActivationPhase } from "@/lib/activation";
import { formatFixedMoney, monthlyFixedPriceMinor } from "@/lib/commercial-prices";
import type { SubscriberPortfolio } from "@/lib/subscriber-contracts";
import { fill } from "@/lib/observatory";

type Item = SubscriberPortfolio["organizations"][number];

export function ActivationView({ portfolio, waiting, phase, busy, onRedeemInvite, onCheckout, onConfirmPayment, onChangeOrganization, onOpenAccount }: {
  portfolio: SubscriberPortfolio;
  waiting: Item[];
  phase: ActivationPhase;
  busy: boolean;
  onRedeemInvite: (token: string) => Promise<boolean>;
  onCheckout: (total: number) => void;
  onConfirmPayment: () => void;
  onChangeOrganization: () => void;
  onOpenAccount: () => void;
}) {
  const { t, locale } = useLocale();
  const [invite, setInvite] = useState("");
  const [inviteError, setInviteError] = useState(false);
  const euros = (cents: number) => formatFixedMoney(locale, PUBLISHED_OFFER, cents);
  const room = capacityRoom(portfolio);
  // Access is active but every confirmed place is in use: only a paid subscription can grow; an invitation does not stack.
  const full = room === 0;
  const pilot = portfolio.entitlementSource === "DESIGN_PARTNER_PILOT";
  // Access exists but cannot be confirmed right now (stale or historical): never offer to buy or redeem again;
  // the only honest step is to check with the owning service, or review payment in the account.
  const unconfirmed = portfolio.capacityCurrentness === "STALE" || portfolio.capacityCurrentness === "HISTORICAL";
  const canSubscribe = portfolio.contractingEnabled && portfolio.canPurchase === true && !(full && pilot) && !unconfirmed;
  const canInvite = room === null && !unconfirmed;
  const total = firstPurchaseTotal(portfolio);
  const working = busy || phase === "redeeming" || phase === "checkout" || phase === "confirming_payment" || phase === "starting";
  const first = waiting[0];
  const name = first ? first.label : "";
  const plural = waiting.length > 1;

  const status: Partial<Record<ActivationPhase, { tone: "progress" | "problem" | "info"; text: string }>> = {
    redeeming: { tone: "progress", text: t("Activando tu invitación…", "Activating your invitation…") },
    starting: { tone: "progress", text: t("Acceso confirmado. Empezando la observación…", "Access confirmed. Starting the observation…") },
    checkout: { tone: "progress", text: t("Abriendo el pago seguro…", "Opening the secure payment…") },
    confirming_payment: { tone: "progress", text: t("Confirmando tu pago con el proveedor de pagos…", "Confirming your payment with the payment provider…") },
    invite_rejected: { tone: "problem", text: t("Esta invitación no es válida o ya ha caducado. Pide un enlace nuevo a quien te invitó; tu organización sigue guardada.", "This invitation is not valid or has expired. Ask whoever invited you for a new link; your organization stays saved.") },
    invite_failed: { tone: "problem", text: t("No pudimos comprobar la invitación ahora mismo. Vuelve a intentarlo en un momento.", "We could not check the invitation right now. Try again in a moment.") },
    checkout_failed: { tone: "problem", text: t("No se pudo abrir el pago. No se ha cobrado nada; vuelve a intentarlo.", "The payment could not be opened. Nothing was charged; try again.") },
    payment_unconfirmed: { tone: "problem", text: t("El pago todavía no aparece confirmado. Si acabas de pagar, puede tardar unos minutos.", "The payment does not appear confirmed yet. If you have just paid, it can take a few minutes.") },
    payment_cancelled: { tone: "info", text: t("Has cancelado el pago. No se ha cobrado nada y tu organización sigue guardada.", "You cancelled the payment. Nothing was charged and your organization stays saved.") },
  };
  const current = status[phase];

  async function submitInvite(event: React.FormEvent) {
    event.preventDefault();
    const token = inviteTokenFrom(invite);
    if (!token) { setInviteError(true); return; }
    setInviteError(false);
    if (await onRedeemInvite(token)) setInvite("");
  }

  return <section className="obs-activation" aria-labelledby="activation-title">
    <div className="obs-activation-saved">
      <span className="obs-activation-lens" aria-hidden="true"><img src="/brand/isotope.svg" alt="" width={40} height={40}/></span>
      <div>
        <h1 id="activation-title">{waiting.length > 1
          ? fill(t("Tus {n} organizaciones están guardadas", "Your {n} organizations are saved"), { n: waiting.length })
          : fill(t("{name} está guardada", "{name} is saved"), { name })}</h1>
        <p>{full
          ? fill(t("Tu acceso cubre {n} y ya está en uso. Empezará en cuanto haya un lugar confirmado; hasta entonces no se consulta nada y no se cobra nada.", "Your access covers {n} and is already in use. It will start as soon as a place is confirmed; until then nothing is looked up and nothing is charged."), { n: portfolio.capacity ?? 0 })
          : plural
            ? t("AXIGNAL empezará a observarlas en cuanto tu acceso esté activo. Hasta entonces no se consulta nada sobre ellas y no se cobra nada.", "AXIGNAL will start observing them as soon as your access is active. Until then nothing is looked up about them and nothing is charged.")
            : t("AXIGNAL empezará a observarla en cuanto tu acceso esté activo. Hasta entonces no se consulta nada sobre ella y no se cobra nada.", "AXIGNAL will start observing it as soon as your access is active. Until then nothing is looked up about it and nothing is charged.")}</p>
      </div>
    </div>

    {current && <div className={`obs-activation-status obs-activation-${current.tone}`} role={current.tone === "problem" ? "alert" : "status"} aria-live="polite">
      <span>{current.text}</span>
      {phase === "payment_unconfirmed" && <button className="obs-link" onClick={onConfirmPayment} disabled={working}>{t("Comprobar de nuevo", "Check again")}</button>}
    </div>}

    <div className="obs-activation-ways">
      {unconfirmed && <article className="obs-activation-way obs-activation-primary">
        <h2><RefreshCw size={18} aria-hidden="true"/>{t("Tu acceso no se puede confirmar ahora", "Your access cannot be confirmed right now")}</h2>
        <p>{t("No asumimos capacidad que no esté confirmada. Vuelve a comprobarlo; si sigue igual, revisa el estado del pago en Cuenta.", "We do not assume capacity that is not confirmed. Check again; if it stays the same, review the payment state in Account.")}</p>
        <div className="obs-activation-actions">
          <button className="obs-button obs-primary" disabled={working} onClick={onConfirmPayment}>{t("Comprobar de nuevo", "Check again")}</button>
          <button className="obs-button" onClick={onOpenAccount}>{t("Cuenta", "Account")}</button>
        </div>
      </article>}
      {canSubscribe &&<article className="obs-activation-way obs-activation-primary">
        <h2><CreditCard size={18} aria-hidden="true"/>{t("Suscripción", "Subscription")}</h2>
        <p className="obs-activation-price"><strong>{euros(FIRST_ORGANIZATION_CENTS)}</strong> <span>{t("al mes por la primera organización", "per month for the first organization")}</span></p>
        <p className="obs-activation-more">{fill(t("{price} al mes por cada organización adicional.", "{price} per month for each additional organization."), { price: euros(ADDITIONAL_ORGANIZATION_CENTS) })}</p>
        {(total > 1 || full) && <p className="obs-activation-total">{fill(t("Total: {price} al mes por {n} organizaciones.", "Total: {price} per month for {n} organizations."), { price: euros(monthlyFixedPriceMinor(PUBLISHED_OFFER, total)), n: total })}</p>}
        <p className="obs-activation-terms">{t("Precios sin impuestos: el proveedor de pago muestra el total con impuestos antes de que confirmes. La observación empieza cuando el pago se verifica.", "Prices exclude tax: the payment provider shows the total with tax before you confirm. The observation starts once the payment is verified.")}</p>
        <button className="obs-button obs-primary" disabled={working} onClick={() => onCheckout(total)}>
          {full ? fill(t("Ampliar a {n} organizaciones", "Expand to {n} organizations"), { n: total }) : t("Continuar al pago seguro", "Continue to secure payment")}<ArrowRight size={16} aria-hidden="true"/>
        </button>
      </article>}

      {canInvite && <article className={`obs-activation-way${canSubscribe ? "" : " obs-activation-primary"}`}>
        <h2><KeyRound size={18} aria-hidden="true"/>{t("Tengo una invitación", "I have an invitation")}</h2>
        <p>{t("Pega el enlace de invitación de Design Partner que recibiste. Activa una organización, sin pago.", "Paste the Design Partner invitation link you received. It activates one organization, with no payment.")}</p>
        <form className="obs-activation-invite" onSubmit={event => void submitInvite(event)}>
          <label htmlFor="activation-invite">{t("Enlace de invitación", "Invitation link")}</label>
          <div className="obs-add-row">
            <input id="activation-invite" value={invite} onChange={event => { setInvite(event.target.value); setInviteError(false); }}
              disabled={working} autoComplete="off" spellCheck={false} aria-invalid={inviteError || undefined} aria-describedby={inviteError ? "activation-invite-error" : undefined}
              placeholder="https://axignal.com/signup#pilot=…"/>
            <button className={`obs-button${canSubscribe ? "" : " obs-primary"}`} disabled={working || !invite.trim()}>{t("Activar invitación", "Activate invitation")}</button>
          </div>
          {inviteError && <p id="activation-invite-error" className="obs-activation-error">{t("Ese texto no es un enlace de invitación de AXIGNAL.", "That text is not an AXIGNAL invitation link.")}</p>}
        </form>
      </article>}

      {!canSubscribe && !unconfirmed && <article className={`obs-activation-way${canInvite ? "" : " obs-activation-primary"}`}>
        {full ? <>
          <h2><Mail size={18} aria-hidden="true"/>{t("¿Necesitas más organizaciones?", "Need more organizations?")}</h2>
          <p>{fill(t("Tu acceso de Design Partner cubre {n}. Cuéntanos qué más quieres observar y te responderemos.", "Your Design Partner access covers {n}. Tell us what else you want to observe and we will reply."), { n: portfolio.capacity ?? 0 })}</p>
        </> : <>
          <h2><Mail size={18} aria-hidden="true"/>{t("¿No tienes invitación?", "No invitation?")}</h2>
          <p>{t("Ahora mismo AXIGNAL se activa con una invitación del programa Design Partner. Cuéntanos qué quieres observar y te responderemos.", "Right now AXIGNAL is activated with a Design Partner programme invitation. Tell us what you want to observe and we will reply.")}</p>
        </>}
        <Link className="obs-button" href="/contact">{t("Solicitar acceso", "Request access")}<ArrowRight size={16} aria-hidden="true"/></Link>
      </article>}
    </div>

    <button className="obs-link obs-activation-change" onClick={onChangeOrganization} disabled={working}>{full ? t("Quitar de la espera", "Remove from the waiting list") : t("Cambiar de organización", "Change organization")}</button>
  </section>;
}
