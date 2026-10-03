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
import { DraftForm } from "./drafts";

type Copy = { es: string; en: string };
const c = (es: string, en: string): Copy => ({ es, en });
export const policyDocuments = [
  {
    slug: "privacy",
    title: c("Privacidad", "Privacy"),
    deck: c(
      "Qué datos hay en esta experiencia, para qué se usan y qué falta antes de publicarla.",
      "Which data this experience uses, why, and what remains before publication.",
    ),
    Icon: Fingerprint,
    sections: [
      {
        title: c("Responsable y alcance", "Controller and scope"),
        text: c(
          "La identidad del responsable, su país y el correo de contacto están pendientes de publicación. Este documento es un borrador para la experiencia local; no sustituye una política aprobada del servicio de producción. Antes de recoger datos reales habrá que completar la información aplicable y validar el tratamiento correspondiente.",
          "The controller's identity, country and contact email are pending publication. This document is a draft for the local experience, not an approved production-service policy. Before collecting real data, applicable disclosures and processing need to be completed and validated.",
        ),
      },
      {
        title: c(
          "Lo que ocurre en esta versión",
          "What happens in this version",
        ),
        text: c(
          "Los formularios de Contacto y GDPR preparan texto en la memoria de esta página. No lo envían al servidor ni registran solicitudes. Las búsquedas de Knowledge y la preferencia de idioma son estados de interfaz. Los contenidos de Panorama son ilustrativos. Los recursos tipográficos y de marca se sirven desde la propia aplicación.",
          "Contact and GDPR forms prepare text in this page's memory. They do not send it to the server or lodge requests. Knowledge searches and language preferences are interface state. Panorama content is illustrative. Typography and brand assets are served by the application itself.",
        ),
      },
      {
        title: c(
          "Finalidades y bases pendientes",
          "Pending purposes and legal bases",
        ),
        text: c(
          "La futura gestión de acceso, consultas, suscripciones y derechos necesita definir sus finalidades, base jurídica y categorías de datos antes de activarse. No asumimos que todo tratamiento se base en consentimiento. Esta versión no activa comunicaciones comerciales, registro de cuentas ni medición publicitaria.",
          "Future access, enquiries, subscriptions and rights handling require defined purposes, legal bases and data categories before activation. We do not assume that every processing activity relies on consent. This version activates no commercial communications, account registration or advertising measurement.",
        ),
      },
      {
        title: c(
          "Destinatarios, transferencias y conservación",
          "Recipients, transfers and retention",
        ),
        text: c(
          "No se han establecido aquí los proveedores, destinatarios, ubicaciones, garantías de transferencia, plazos de conservación ni las prácticas de registros del despliegue de producción. Deben documentarse por tratamiento. No prometemos una ubicación, un plazo o una ausencia de registros que esta interfaz no puede verificar.",
          "Production providers, recipients, locations, transfer safeguards, retention periods and deployment logging practices have not been established here. They must be documented per processing activity. We do not promise a location, period or absence of logs this interface cannot verify.",
        ),
      },
      {
        title: c("Derechos y solicitudes", "Rights and requests"),
        text: c(
          "El centro GDPR explica los derechos y permite preparar un borrador. El canal del responsable sigue pendiente. Una descarga no acredita recepción. Una solicitud real debe evaluarse conforme a la normativa aplicable, también cuando la información proceda de fuentes públicas. La arquitectura de memoria compartida no sustituye esa evaluación.",
          "The GDPR centre explains rights and lets you prepare a draft. The controller's channel remains pending. A download does not prove receipt. A real request must be assessed under applicable law, including information originating in public sources. Shared-memory architecture does not replace that assessment.",
        ),
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
        title: c("Una experiencia de revisión", "An experience for review"),
        text: c(
          "Estas condiciones son un borrador informativo de la experiencia local. El titular, país, condiciones contractuales, oferta y procedimiento de contratación están pendientes. Acceder a la demo o descargar un borrador no crea una cuenta, una suscripción ni la aceptación de un contrato de pago.",
          "These terms are an informational draft for the local experience. The operator, country, contractual terms, offer and contracting procedure remain pending. Opening the demo or downloading a draft creates neither an account nor a subscription or acceptance of a paid contract.",
        ),
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
        text: c(
          "Seleccionar una organización dirige un foco de observación; no permite editar su verdad económica. Panorama presenta una proyección humana del mundo canónico. AXENT ayuda a investigar y explicar sin autoridad para admitir hechos. Los permisos privados, la identidad y la suscripción requieren sus servicios propietarios.",
          "Selecting an organization directs an observation focus; it does not authorize editing its economic truth. Panorama presents a human projection of the canonical world. AXENT helps research and explain without authority to admit facts. Private permissions, identity and subscriptions require their owning services.",
        ),
      },
      {
        title: c(
          "Disponibilidad e integraciones",
          "Availability and integrations",
        ),
        text: c(
          "La demo identifica sus datos ilustrativos. El acceso Google y ChatGPT está preparado, pero no conectado. Contacto y GDPR generan borradores locales. Ninguna de estas superficies garantiza investigación ejecutada, autenticación o recepción de solicitudes. Las condiciones finales deberán describir el servicio realmente operativo.",
          "The demo labels its illustrative data. Google and ChatGPT access is prepared but not connected. Contact and GDPR generate local drafts. None of these surfaces guarantees completed research, authentication or receipt of requests. Final terms must describe the actually operational service.",
        ),
      },
    ],
  },
  {
    slug: "cookies",
    title: c("Cookies y almacenamiento", "Cookies and storage"),
    deck: c(
      "Una vista concreta de lo que esta aplicación guarda y lo que aún no está conectado.",
      "A concrete view of what this application stores and what is not yet connected.",
    ),
    Icon: Cookie,
    sections: [
      {
        title: c("Alcance de este inventario", "Scope of this inventory"),
        text: c(
          "Este inventario describe el código de la experiencia local. No acredita las prácticas de una futura infraestructura, proxy o proveedor. Esta aplicación no implementa cookies analíticas o publicitarias, ni integra píxeles de terceros. Las fuentes se alojan localmente.",
          "This inventory describes the local experience's code. It does not establish the practices of future infrastructure, a proxy or a provider. This application implements no analytics or advertising cookies and integrates no third-party pixels. Fonts are hosted locally.",
        ),
      },
      {
        title: c(
          "Qué se guarda y qué permanece en la página",
          "What is stored and what stays in the page",
        ),
        text: c(
          "El idioma se guarda localmente como preferencia hasta que lo cambies o borres los datos del sitio. El cierre del aviso de privacidad se recuerda hasta 180 días. La búsqueda editorial y los borradores permanecen solo como estado de la página. Los borradores no se guardan en localStorage, cookies o base de datos por esta aplicación. Cambiar de página o cerrar la pestaña descarta el borrador. El navegador puede aplicar sus propias funciones de autocompletado, independientes del almacenamiento de AXIGNAL.",
          "Your language is stored locally as a preference until you change it or clear site data. Privacy notice dismissal is remembered for up to 180 days. Editorial search and drafts remain only as page state. This application does not save drafts in localStorage, cookies or a database. Leaving the page or closing the tab discards the draft. A browser may apply its own autofill features, independently of AXIGNAL storage.",
        ),
      },
      {
        title: c(
          "Acceso y preferencias futuras",
          "Future access and preferences",
        ),
        text: c(
          "No hay sesión autenticada conectada ni cookie de acceso emitida por estos flujos preparados. Cuando se active el servicio, habrá que inventariar almacenamiento necesario, duración y proveedor. Si se incorporan tecnologías opcionales, las decisiones de la persona deberán ser claras, revocables y efectivamente respetadas antes de activarlas.",
          "These prepared flows connect no authenticated session and issue no sign-in cookie. Activating the service requires an inventory of necessary storage, duration and provider. If optional technologies are introduced, people's choices must be clear, revocable and actually respected before activation.",
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
          <Observer />
          <span className="hand-note">
            {t("la letra pequeña, bien visible", "fine print, clearly visible")}
          </span>
        </div>
      </section>
      <div className="publication-banner">
        <Info size={20} />
        <div>
          <strong>{t("Antes de publicar", "Before publication")}</strong>
          <p>
            {t(
              "Responsable, país y correo público pendientes. Estos textos son borradores de revisión y no una certificación de cumplimiento.",
              "Controller, country and public email are pending. These texts are review drafts and not a compliance certification.",
            )}
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
              {t("Leer borrador", "Read draft")}
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
            <h3>{t("Información pendiente", "Pending information")}</h3>
            <p>
              {t(
                "Responsable, país, correo de contacto y validación jurídica del servicio: pendientes de publicación.",
                "Controller, country, contact email and legal review of the service: pending publication.",
              )}
            </p>
            <Link href="/contact" className="text-link">
              {t("Preparar una consulta", "Prepare an enquiry")}
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
    id: "automated",
    title: c("Decisiones automatizadas", "Automated decisions"),
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
            {t(
              "Conoce tus derechos, entiende los límites de esta versión y prepara una solicitud con tus propias palabras.",
              "Know your rights, understand this version's limits and prepare a request in your own words.",
            )}
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
            {t("Del derecho al borrador", "From a right to a draft")}
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
                "Canal pendiente de publicación",
                "Channel pending publication",
              )}
            </strong>
            <p>
              {t(
                "El responsable y su correo aún no están definidos. Este borrador no inicia plazos ni acredita recepción. Una solicitud real debe llegar al canal habilitado del responsable.",
                "The controller and email are not yet defined. This draft neither starts response deadlines nor proves receipt. A real request must reach the controller's designated channel.",
              )}
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
            {t("Leer el borrador de privacidad", "Read the privacy draft")}
            <ArrowRight size={16} />
          </Link>
        </div>
        <DraftForm
          subject={
            t("Solicitud de ", "Request for ") + copy(rights[selected].title)
          }
          rights
        />
      </section>
    </PublicShell>
  );
}
