"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  ArrowLeft,
  FileText,
  ShieldCheck,
  Fingerprint,
  Cookie,
  BookOpen,
  Check,
  Info,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import { Observer } from "./ui";
import { PublicShell, PublicationNote } from "./public-shell";
import { PublicRequestChannel } from "./public-request-channel";

type Copy = { es: string; en: string };
const c = (es: string, en: string): Copy => ({ es, en });
export const policyDocuments = [
  {
    slug: "privacy",
    title: c("Privacidad", "Privacy"),
    deck: c("Qué datos utiliza AXIGNAL y cómo ejercer tus derechos.", "Which details AXIGNAL uses and how to exercise your rights."),
    Icon: Fingerprint,
    sections: [
      {
        title: c("Responsable y alcance", "Controller and scope"),
        text: c("Responsable: AXIGNAL. País: España. El canal de contacto muestra un correo público sólo cuando el servicio lo publica. No se ha publicado un NIF.", "Controller: AXIGNAL. Country: Spain. The contact channel shows a public email only when the service publishes one. No tax identifier has been published."),
      },
      {
        title: c(
          "Lo que ocurre en esta versión",
          "What happens in this version",
        ),
        text: c("Contacto y GDPR consultan la disponibilidad del canal. Cuando está habilitado, el envío registra una solicitud privada con su aviso y referencia; no modifica la verdad económica. Panorama es un ejemplo ficticio identificado.", "Contact and GDPR check channel availability. When enabled, submission registers a private request with its notice and reference; it does not change economic truth. Panorama is a labelled fictional example."),
      },
      {
        title: c(
          "Finalidades del tratamiento",
          "Processing purposes",
        ),
        text: c("Los datos de contacto se utilizan para gestionar tu solicitud. El acceso solicita identidad básica al proveedor disponible. Las comunicaciones opcionales requieren una decisión separada; una consulta no te suscribe.", "Contact details are used to handle your request. Access asks the available provider for basic identity. Optional communications require a separate decision; an enquiry does not subscribe you."),
      },
      {
        title: c(
          "Destinatarios, transferencias y conservación",
          "Recipients, transfers and retention",
        ),
        text: c("Las solicitudes de Contacto y GDPR se conservan 90 días. La entrega depende de un canal autorizado por AXIGNAL y puede fallar después del registro. El recibo no garantiza entrega ni resolución.", "Contact and GDPR requests are retained for 90 days. Delivery depends on an AXIGNAL-authorized channel and may fail after registration. The receipt does not guarantee delivery or resolution."),
      },
      {
        title: c("Derechos y solicitudes", "Rights and requests"),
        text: c("GDPR permite solicitar acceso, rectificación, supresión, limitación, oposición, portabilidad u otros derechos cuando el canal está habilitado. El recibo acredita registro, no aceptación legal. Cada solicitud necesita valoración humana.", "GDPR supports access, rectification, erasure, restriction, objection, portability or other rights requests when the channel is enabled. The receipt confirms registration, not legal acceptance. Each request needs human assessment."),
      },
    ],
  },
  {
    slug: "terms",
    title: c("Uso y límites", "Use and limitations"),
    deck: c(
      "Qué puedes explorar, qué es ilustrativo y qué no constituye una conclusión comercial.",
      "What you can explore, what is illustrative and what is not a commercial conclusion.",
    ),
    Icon: FileText,
    sections: [
      {
        title: c("Uso del servicio", "Using the service"),
        text: c("AXIGNAL opera desde España. Abrir el ejemplo o enviar una consulta no crea una suscripción ni acepta un contrato de pago. La contratación depende de su disponibilidad y autorización propias.", "AXIGNAL operates from Spain. Opening the example or sending an enquiry does not create a subscription or accept a paid contract. Contracting depends on its own availability and authorization."),
      },
      {
        title: c("Observación y posibilidad", "Observation and possibility"),
        text: c(
          "AXIGNAL orienta comprensión económica. Una señal potencial no acredita un cliente, una adjudicación, una relación comercial o un resultado futuro. Una ausencia de evidencia no equivale a una respuesta falsa. Revisa el alcance, la fuente y la temporalidad antes de interpretar una lectura material.",
          "AXIGNAL supports economic understanding. A potential signal does not establish a customer, an award, a commercial relationship or a future outcome. Missing evidence is not a false answer. Review scope, sources and time before interpreting a material reading.",
        ),
      },
      {
        title: c(
          "Tu atención y el mundo compartido",
          "Your attention and the shared world",
        ),
        text: c("Seleccionar una organización dirige atención; no permite editar su verdad económica. El ejemplo público utiliza datos ficticios. La identidad, los permisos y las suscripciones pertenecen a sus servicios privados.", "Selecting an organization directs attention; it does not authorize editing economic truth. The public example uses fictional data. Identity, permissions and subscriptions belong to their private services."),
      },
      {
        title: c(
          "Disponibilidad e integraciones",
          "Availability and integrations",
        ),
        text: c("El ejemplo es ficticio. Acceder y crear cuenta consultan el estado real de cada proveedor. Contacto y GDPR sólo permiten enviar cuando el canal está habilitado. Un recibo confirma registro, sin garantizar entrega o resolución.", "The example is fictional. Sign-in and signup check each provider’s actual status. Contact and GDPR allow submission only when their channel is enabled. A receipt confirms registration without guaranteeing delivery or resolution."),
      },
    ],
  },
  {
    slug: "cookies",
    title: c("Cookies y almacenamiento", "Cookies and storage"),
    deck: c("Qué guarda esta aplicación y cómo se utiliza.", "What this application stores and how it is used."),
    Icon: Cookie,
    sections: [
      {
        title: c("Alcance de este inventario", "Scope of this inventory"),
        text: c("La aplicación utiliza almacenamiento necesario y preferencias de interfaz. Las fuentes se sirven localmente. No activa cookies publicitarias ni píxeles de terceros.", "The application uses necessary storage and interface preferences. Fonts are served locally. It does not activate advertising cookies or third-party pixels."),
      },
      {
        title: c(
          "Qué se guarda y qué permanece en la página",
          "What is stored and what stays in the page",
        ),
        text: c("El idioma se guarda como preferencia local. El cierre del aviso se recuerda hasta 180 días. El texto de una solicitud permanece en la página hasta enviarlo; después, el registro se conserva en el servidor durante 90 días. El navegador puede utilizar autocompletado.", "Language is stored as a local preference. Notice dismissal is remembered for up to 180 days. Request text stays on the page until submitted; the server then retains the record for 90 days. Your browser may use autofill."),
      },
      {
        title: c(
          "Acceso y preferencias",
          "Access and preferences",
        ),
        text: c("La autenticación utiliza cookies necesarias HttpOnly, Secure y SameSite Lax para la transacción y la sesión. La sesión depende de su vigencia y de la validación del runtime; el navegador no concede permisos.", "Authentication uses necessary HttpOnly, Secure and SameSite Lax cookies for the transaction and session. The session depends on its validity and runtime validation; the browser does not grant permissions."),
      },
      {
        title: c("Sesión privada de Admin", "Private Admin session"),
        text: c(
          "Customer Zero transporta una sesión Admin existente en una cookie HttpOnly y SameSite Strict, hasta ocho horas. El runtime comprueba de nuevo su vigencia y alcance en cada solicitud; la cookie no concede autoridad económica.",
          "Customer Zero transports an existing Admin session in an HttpOnly, SameSite Strict cookie for up to eight hours. The runtime checks its validity and scope on every request; the cookie grants no economic authority.",
        ),
      },
    ],
  },
];
export function Policies() {
  const { t, copy } = useLocale();
  return (
    <PublicShell className="trust-page">
      <section className="public-intro trust-intro">
        <div>
          <span className="eyebrow">
            {t(
              "Políticas / El centro de confianza",
              "Policies / The trust centre",
            )}
          </span>
          <h1>
            {t("La confianza también", "Trust also")}
            <br />
            <em>{t("necesita contexto.", "needs context.")}</em>
          </h1>
          <p>
            {t(
              "Un lugar para entender tus datos, el alcance de AXIGNAL y las fronteras que cuidan cada lectura.",
              "A place to understand your data, AXIGNAL's scope and the boundaries protecting each reading.",
            )}
          </p>
          <PublicationNote />
        </div>
        <div className="trust-illustration">
          <div className="trust-paper">
            <ShieldCheck size={27} />
            <span>
              {t("Claridad sobre", "Clarity about")}
              <br />
              {t("lo que importa.", "what matters.")}
            </span>
            <i />
            <i />
            <i />
          </div>
          <Observer scene="boundaries" />
          <span className="hand-note">
            {t("la letra pequeña, bien visible", "fine print, clearly visible")}
          </span>
        </div>
      </section>
      <div className="publication-banner">
        <Info size={20} />
        <div>
          <strong>{t("Información del servicio", "Service information")}</strong>
          <p>
            {t("Responsable: AXIGNAL · España. Estos textos describen funciones y límites; no certifican cumplimiento jurídico.", "Controller: AXIGNAL · Spain. These texts describe functions and limits; they do not certify legal compliance.")}
          </p>
        </div>
      </div>
      <section
        className="policy-directory"
        aria-label={t("Documentos de políticas", "Policy documents")}
      >
        {policyDocuments.map((doc) => (
          <Link href={"/policies/" + doc.slug} key={doc.slug}>
            <doc.Icon size={26} />
            <div>
              <h2>{copy(doc.title)}</h2>
              <p>{copy(doc.deck)}</p>
            </div>
            <span className="policy-link-end">
              {t("Leer documento", "Read document")}
              <ArrowUpRight size={20} />
            </span>
          </Link>
        ))}
      </section>
      <section className="rights-invitation">
        <div>
          <span className="eyebrow">
            {t("Datos personales / GDPR", "Personal data / GDPR")}
          </span>
          <h2>
            {t("Comprender es también", "Understanding also means")}
            <br />
            <em>{t("conocer tus derechos.", "knowing your rights.")}</em>
          </h2>
          <p>
            {t(
              "Explora qué puedes solicitar, qué información necesita una petición y cómo preparar tu texto.",
              "Explore what you can request, what a request needs and how to prepare your text.",
            )}
          </p>
          <Link className="button primary" href="/gdpr">
            {t("Mis datos y derechos", "My data and rights")}
            <ArrowRight size={18} />
          </Link>
        </div>
        <div className="rights-summary">
          <Fingerprint size={36} />
          <h3>
            {t(
              "Tu contexto privado tiene su propia frontera.",
              "Your private context has its own boundary.",
            )}
          </h3>
          <p>
            {t(
              "La memoria económica compartida no mezcla tu identidad, tus permisos o tus conversaciones privadas con la verdad del mundo observado.",
              "Shared economic memory does not mix your identity, permissions or private conversations with the truth of the observed world.",
            )}
          </p>
        </div>
      </section>
    </PublicShell>
  );
}
export function PolicyDocument({ slug }: { slug: string }) {
  const { t, copy } = useLocale();
  const doc = policyDocuments.find((d) => d.slug === slug)!;
  return (
    <PublicShell className="policy-page">
      <header className="policy-intro">
        <Link href="/policies" className="text-link">
          <ArrowLeft size={16} />
          {t("Centro de confianza", "Trust centre")}
        </Link>
        <div>
          <doc.Icon size={30} />
          <PublicationNote />
        </div>
        <h1>{copy(doc.title)}</h1>
        <p>{copy(doc.deck)}</p>
      </header>
      <div className="article-reading policy-reading">
        <nav
          className="reading-rail"
          aria-label={t("Índice del documento", "Document contents")}
        >
          <span className="eyebrow">
            {t("En este documento", "In this document")}
          </span>
          {doc.sections.map((s, i) => (
            <a href={"#policy-" + i} key={i}>
              {copy(s.title)}
            </a>
          ))}
          <Link href="/gdpr">
            {t("Mis datos y derechos", "My data and rights")}
          </Link>
        </nav>
        <article className="article-prose">
          {doc.sections.map((s, i) => (
            <section id={"policy-" + i} key={i}>
              <h2>{copy(s.title)}</h2>
              <p>{copy(s.text)}</p>
            </section>
          ))}
          <aside className="article-basis">
            <Info size={20} />
            <h3>{t("Responsable y límites", "Controller and limits")}</h3>
            <p>
              {t("Responsable: AXIGNAL · España. El correo depende del estado del canal; no se publica un NIF ni se garantiza una resolución legal automática.", "Controller: AXIGNAL · Spain. Email depends on channel status; no tax identifier is published and no automatic legal resolution is guaranteed.")}
            </p>
            <Link href="/contact" className="text-link">
              {t("Consultar el canal", "Check the channel")}
              <ArrowRight size={16} />
            </Link>
          </aside>
        </article>
      </div>
    </PublicShell>
  );
}
const rights = [
  {
    id: "access",
    title: c("Acceso", "Access"),
    text: c(
      "Conocer si se tratan tus datos y obtener acceso a ellos y a la información del tratamiento.",
      "Learn whether your data is processed and access the data and processing information.",
    ),
  },
  {
    id: "rectification",
    title: c("Rectificación", "Rectification"),
    text: c(
      "Solicitar que se corrijan datos personales inexactos o se completen datos incompletos.",
      "Request correction of inaccurate personal data or completion of incomplete data.",
    ),
  },
  {
    id: "erasure",
    title: c("Supresión", "Erasure"),
    text: c(
      "Solicitar la eliminación cuando proceda. La petición necesita valorar las condiciones y excepciones aplicables.",
      "Request deletion where applicable. The request requires assessment of relevant conditions and exceptions.",
    ),
  },
  {
    id: "restriction",
    title: c("Limitación", "Restriction"),
    text: c(
      "Solicitar que se restrinja el tratamiento en los supuestos previstos por la normativa.",
      "Request that processing be restricted in the situations provided by law.",
    ),
  },
  {
    id: "portability",
    title: c("Portabilidad", "Portability"),
    text: c(
      "Solicitar datos en un formato adecuado y su transmisión cuando se cumplan las condiciones del derecho.",
      "Request data in an appropriate format and transmission when the conditions for this right are met.",
    ),
  },
  {
    id: "objection",
    title: c("Oposición", "Objection"),
    text: c(
      "Oponerte a determinados tratamientos según su base y circunstancias. El responsable debe valorar la petición.",
      "Object to certain processing depending on its basis and circumstances. The controller must assess the request.",
    ),
  },
  {
    id: "other",
    title: c("Otros derechos", "Other rights"),
    text: c(
      "Conocer las garantías frente a decisiones exclusivamente automatizadas con efectos jurídicos o de importancia similar.",
      "Understand safeguards concerning solely automated decisions with legal or similarly significant effects.",
    ),
  },
];
export function GDPR() {
  const { t, copy } = useLocale();
  const [selected, setSelected] = useState(0);
  return (
    <PublicShell className="gdpr-page">
      <section className="public-intro gdpr-intro">
        <div>
          <span className="eyebrow">
            GDPR / {t("Tus datos y derechos", "Your data and rights")}
          </span>
          <h1>
            {t("Una mirada clara", "A clear perspective")}
            <br />
            <em>{t("sobre tus datos.", "on your data.")}</em>
          </h1>
          <p>
            {t("Conoce tus derechos y comprueba el canal para presentar tu solicitud.", "Know your rights and check the channel to submit your request.")}
          </p>
          <PublicationNote />
        </div>
        <div className="gdpr-principle">
          <Fingerprint size={40} />
          <h2>
            {t("Tu identidad.", "Your identity.")}
            <br />
            {t("Tu contexto privado.", "Your private context.")}
          </h2>
          <p>
            {t(
              "Son distintos de una organización económica y de la memoria del mundo observado.",
              "They are distinct from an economic organization and the memory of the observed world.",
            )}
          </p>
          <span className="hand-note">
            {t("cada cosa, en su lugar", "each thing in its place")}
          </span>
        </div>
      </section>
      <section className="rights-section">
        <div className="index-heading">
          <h2>
            {t(
              "Los derechos, en lenguaje humano.",
              "Your rights, in human language.",
            )}
          </h2>
          <a
            className="text-link"
            href="https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("Referencia EDPB", "EDPB reference")}
            <ArrowUpRight size={16} />
            <span className="sr-only">{t("Nueva pestaña", "New tab")}</span>
          </a>
        </div>
        <p className="rights-scope">
          {t(
            "Su aplicación depende del tratamiento y de las condiciones legales. Esta explicación no decide tu caso.",
            "Applicability depends on the processing and legal conditions. This explanation does not decide your case.",
          )}
        </p>
        <div
          className="rights-selector"
          role="group"
          aria-label={t(
            "Derecho que quieres explorar",
            "Right you want to explore",
          )}
        >
          {rights.map((right, i) => (
            <button
              key={right.id}
              aria-pressed={selected === i}
              onClick={() => setSelected(i)}
            >
              <span>{copy(right.title)}</span>
              {selected === i ? <Check size={16} /> : <ArrowRight size={16} />}
            </button>
          ))}
        </div>
        <div className="rights-explanation" role="status">
          <Fingerprint size={25} />
          <div>
            <h3>{copy(rights[selected].title)}</h3>
            <p>{copy(rights[selected].text)}</p>
          </div>
        </div>
      </section>
      <section className="rights-request">
        <div className="rights-request-copy">
          <span className="eyebrow">
            {t("Del derecho a la solicitud", "From a right to a request")}
          </span>
          <h2>
            {t("Dale forma", "Put your request")}
            <br />
            <em>{t("a tu solicitud.", "into words.")}</em>
          </h2>
          <p>
            {t(
              "Describe qué datos o tratamiento te preocupan. No necesitas subir un documento de identidad a esta página.",
              "Describe which data or processing concerns you. You do not need to upload an identity document here.",
            )}
          </p>
          <div className="rights-channel">
            <Info size={21} />
            <strong>
              {t(
                "Disponibilidad del canal",
                "Channel availability",
              )}
            </strong>
            <p>
              {t("Responsable: AXIGNAL · España. El formulario comprueba el estado del canal. Recibir una solicitud no supone aceptarla ni resolverla; la evaluación es humana.", "Controller: AXIGNAL · Spain. The form checks channel status. Receiving a request does not mean accepting or resolving it; assessment is human.")}
            </p>
          </div>
          <p>
            {t(
              "La información pública también puede contener datos personales. La arquitectura de AXIGNAL no impide una valoración legal de acceso, rectificación o supresión.",
              "Public information may also contain personal data. AXIGNAL's architecture does not prevent a legal assessment of access, rectification or erasure.",
            )}
          </p>
          <a
            className="text-link"
            href="https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0105-que-derechos-reconoce-el-rgpd-a-los-afectados"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("Conocer los derechos · AEPD", "Learn about rights · AEPD")}
            <ArrowUpRight size={16} />
            <span className="sr-only">{t("Nueva pestaña", "New tab")}</span>
          </a>
          <Link href="/policies/privacy" className="text-link">
            {t("Leer la información de privacidad", "Read the privacy information")}
            <ArrowRight size={16} />
          </Link>
        </div>
        <PublicRequestChannel
          subject={
            t("Solicitud de ", "Request for ") + copy(rights[selected].title)
          }
          key={rights[selected].id}
          category={rights[selected].id as "access" | "rectification" | "erasure" | "restriction" | "portability" | "objection" | "other"}
        />
      </section>
    </PublicShell>
  );
}
