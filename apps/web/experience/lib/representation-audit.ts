/** Fixed copy for the representation audit (representation-audit.v1). Never generated:
 * each check says what was observed, why it matters and what the organization can do.
 * Nothing here is a ranking, a traffic estimate or a score. */
type Translate = (es: string, en: string) => string;

export type AuditCopy = { title: string; why: string; action: string };

export function auditSection(id: string, t: Translate): string {
  switch (id) {
    case "SEARCH_FINDABILITY": return t("Encontrabilidad en buscadores", "Search findability");
    case "AI_ANSWER_READINESS": return t("Preparación para respuestas de IA", "AI answer readiness");
    case "SHARING_AND_MOBILE": return t("Compartir y móvil", "Sharing and mobile");
    default: return id;
  }
}

export function auditStatus(id: string, t: Translate): string {
  switch (id) {
    case "PASS": return t("Correcto", "OK");
    case "ATTENTION": return t("Conviene revisar", "Worth reviewing");
    case "UNKNOWN": return t("No observado", "Not observed");
    default: return t("No aplica", "Not applicable");
  }
}

export function auditImpact(id: string, t: Translate): string {
  return id === "HIGH" ? t("Impacto alto", "High impact") : id === "MEDIUM" ? t("Impacto medio", "Medium impact") : t("Impacto bajo", "Low impact");
}

export function auditCopy(id: string, t: Translate): AuditCopy {
  switch (id) {
    case "ROBOTS_TXT_PUBLISHED": return {
      title: t("No publica robots.txt", "It publishes no robots.txt"),
      why: t("Sin él, los rastreadores aplican sus reglas por defecto y no hay dónde declarar el sitemap.", "Without it, crawlers apply their defaults and there is nowhere to declare the sitemap."),
      action: t("Publica /robots.txt con las reglas de acceso y la línea Sitemap.", "Publish /robots.txt with access rules and a Sitemap line.") };
    case "SEARCH_CRAWLERS_ALLOWED": return {
      title: t("Su robots.txt bloquea a buscadores", "Its robots.txt blocks search engines"),
      why: t("Un buscador bloqueado no puede leer la web para representarla.", "A blocked search engine cannot read the site to represent it."),
      action: t("Revisa las reglas Disallow de Googlebot y Bingbot.", "Review the Disallow rules for Googlebot and Bingbot.") };
    case "SITEMAP_DECLARED": return {
      title: t("No declara un sitemap", "It declares no sitemap"),
      why: t("El sitemap ayuda a descubrir todas sus páginas, no solo las enlazadas.", "A sitemap helps discover every page, not only the linked ones."),
      action: t("Publica un sitemap.xml y decláralo en robots.txt.", "Publish a sitemap.xml and declare it in robots.txt.") };
    case "SITEMAP_READABLE": return {
      title: t("Su sitemap no se pudo leer o está vacío", "Its sitemap could not be read or is empty"),
      why: t("Un sitemap declarado que no funciona no ayuda a descubrir páginas.", "A declared sitemap that does not work does not help discover pages."),
      action: t("Comprueba que la URL del sitemap responde con XML válido y lista sus páginas.", "Check that the sitemap URL answers with valid XML listing its pages.") };
    case "HOMEPAGE_CANONICAL_SAME_SITE": return {
      title: t("La portada no declara una URL canónica propia", "The homepage declares no canonical URL of its own"),
      why: t("Sin canónica, o con una de otro dominio, los buscadores pueden elegir otra versión de la página.", "Without a canonical, or with one on another domain, search engines may pick another version of the page."),
      action: t("Añade <link rel=\"canonical\"> apuntando a su propia URL.", "Add <link rel=\"canonical\"> pointing to its own URL.") };
    case "TITLES_PRESENT_AND_SIZED": return {
      title: t("Hay páginas sin título o con un título demasiado corto o largo", "Some pages have no title or one that is too short or long"),
      why: t("El título es lo primero que muestran buscadores y asistentes; entre 15 y 65 caracteres se lee completo.", "The title is the first thing search engines and assistants show; 15 to 65 characters read in full."),
      action: t("Escribe un título por página que diga qué ofrece y dónde.", "Write one title per page saying what it offers and where.") };
    case "TITLES_DISTINCT": return {
      title: t("Varias páginas comparten el mismo título", "Several pages share the same title"),
      why: t("Títulos repetidos hacen que las páginas compitan entre sí y se distingan peor.", "Repeated titles make pages compete with each other and harder to tell apart."),
      action: t("Da a cada página un título que describa su contenido concreto.", "Give each page a title describing its own content.") };
    case "DESCRIPTIONS_PRESENT_AND_SIZED": return {
      title: t("Faltan descripciones o no tienen una longitud útil", "Descriptions are missing or not a useful length"),
      why: t("La meta descripción suele ser el resumen que se muestra; entre 50 y 170 caracteres.", "The meta description is often the summary shown; 50 to 170 characters."),
      action: t("Añade una descripción por página con su propuesta de valor.", "Add one description per page with its value proposition.") };
    case "ONE_H1_PER_PAGE": return {
      title: t("Hay páginas sin un único encabezado principal (H1)", "Some pages lack a single main heading (H1)"),
      why: t("Un H1 claro dice a máquinas y personas de qué trata la página.", "A clear H1 tells machines and people what the page is about."),
      action: t("Deja un solo H1 por página con su tema principal.", "Keep one H1 per page with its main topic.") };
    case "HTTPS": return {
      title: t("Hay páginas servidas sin HTTPS", "Some pages are served without HTTPS"),
      why: t("Sin HTTPS los navegadores avisan de que no es seguro y la confianza baja.", "Without HTTPS browsers warn that it is not secure and trust drops."),
      action: t("Sirve todo el sitio por HTTPS y redirige HTTP.", "Serve the whole site over HTTPS and redirect HTTP.") };
    case "LANGUAGE_DECLARED": return {
      title: t("No declara el idioma de la página", "It does not declare the page language"),
      why: t("El atributo lang ayuda a mostrar la página a quien busca en ese idioma.", "The lang attribute helps show the page to people searching in that language."),
      action: t("Añade lang al elemento <html>, por ejemplo lang=\"es\".", "Add lang to the <html> element, for example lang=\"es\".") };
    case "HREFLANG_X_DEFAULT": return {
      title: t("Sus versiones de idioma no declaran una versión por defecto", "Its language versions declare no default"),
      why: t("Sin x-default, quien llega en otro idioma puede ver una versión poco adecuada.", "Without x-default, visitors in another language may see an unsuitable version."),
      action: t("Añade hreflang=\"x-default\" a la versión general.", "Add hreflang=\"x-default\" to the general version.") };
    case "AI_CRAWLERS_ALLOWED": return {
      title: t("Su robots.txt bloquea a rastreadores de asistentes de IA", "Its robots.txt blocks AI assistant crawlers"),
      why: t("Un asistente que no puede leer la web no puede usarla al responder sobre su sector. Puede ser una decisión deliberada.", "An assistant that cannot read the site cannot use it when answering about its sector. It may be a deliberate choice."),
      action: t("Decide qué asistentes pueden leerla y ajusta robots.txt en consecuencia.", "Decide which assistants may read it and adjust robots.txt accordingly.") };
    case "ORGANIZATION_DECLARED": return {
      title: t("No se declara como organización en datos estructurados", "It does not declare itself as an organization in structured data"),
      why: t("Buscadores y asistentes identifican mejor una entidad que se describe a sí misma (schema.org Organization).", "Search engines and assistants identify better an entity that describes itself (schema.org Organization)."),
      action: t("Añade un bloque JSON-LD Organization con nombre, web, logo y contacto.", "Add an Organization JSON-LD block with name, website, logo and contact.") };
    case "ORGANIZATION_COMPLETE": return {
      title: t("Su ficha de organización está incompleta", "Its organization record is incomplete"),
      why: t("Nombre, web, logo, perfiles, dirección y contacto permiten reconocer la entidad sin ambigüedad.", "Name, website, logo, profiles, address and contact let the entity be recognized unambiguously."),
      action: t("Completa en su JSON-LD los campos que faltan.", "Complete the missing fields in its JSON-LD.") };
    case "ENTITY_PROFILES_LINKED": return {
      title: t("No enlaza sus perfiles oficiales (sameAs)", "It does not link its official profiles (sameAs)"),
      why: t("Enlazar LinkedIn, Wikipedia u otros perfiles ayuda a conectar todas sus menciones con la misma entidad.", "Linking LinkedIn, Wikipedia or other profiles helps tie all its mentions to the same entity."),
      action: t("Añade sameAs con al menos dos perfiles oficiales.", "Add sameAs with at least two official profiles.") };
    case "FAQ_OR_QA_DECLARED": return {
      title: t("No publica preguntas frecuentes estructuradas", "It publishes no structured FAQ"),
      why: t("Las preguntas y respuestas claras son fáciles de citar al responder dudas de clientes.", "Clear questions and answers are easy to cite when answering customer questions."),
      action: t("Publica una página de preguntas frecuentes con FAQPage en JSON-LD.", "Publish an FAQ page with FAQPage JSON-LD.") };
    case "STRUCTURED_DATA_PARSES": return {
      title: t("Parte de sus datos estructurados no se puede leer", "Part of its structured data cannot be read"),
      why: t("Un bloque JSON-LD con errores se ignora entero.", "A JSON-LD block with errors is ignored entirely."),
      action: t("Valida sus bloques JSON-LD y corrige los errores de sintaxis.", "Validate its JSON-LD blocks and fix syntax errors.") };
    case "LLMS_TXT_PUBLISHED": return {
      title: t("No publica llms.txt", "It publishes no llms.txt"),
      why: t("Es una convención emergente para resumir a asistentes de IA qué es y qué ofrece. No es un estándar ni garantiza nada.", "It is an emerging convention to summarize for AI assistants what it is and offers. It is not a standard and guarantees nothing."),
      action: t("Valora publicar /llms.txt con su descripción y enlaces clave.", "Consider publishing /llms.txt with its description and key links.") };
    case "HOMEPAGE_TEXT_DEPTH": return {
      title: t("Su portada tiene poco texto legible", "Its homepage has little readable text"),
      why: t("Con poco texto, máquinas y personas tienen menos base para entender qué hace.", "With little text, machines and people have less basis to understand what it does."),
      action: t("Explica en la portada qué hace, para quién y dónde, en texto (no solo imágenes).", "Explain on the homepage what it does, for whom and where, in text (not only images).") };
    case "ACTIVITY_STATED_IN_TEXT": return {
      title: t("Su actividad no se reconoce en el texto de su web", "Its activity is not recognized in its website text"),
      why: t("Si una lectura automática no reconoce a qué se dedica, un asistente tampoco podrá relacionarla.", "If an automated reading cannot recognize what it does, an assistant may not connect it either."),
      action: t("Di con palabras claras qué servicio o producto ofrece.", "State in plain words what service or product it offers.") };
    case "MOBILE_VIEWPORT": return {
      title: t("La portada no está preparada para móvil (viewport)", "The homepage is not set up for mobile (viewport)"),
      why: t("Sin viewport, en el móvil se ve diminuta; la mayoría de visitas llegan desde el móvil.", "Without a viewport it renders tiny on phones; most visits come from mobile."),
      action: t("Añade <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.", "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.") };
    case "SOCIAL_PREVIEW_TAGS": return {
      title: t("Al compartirla, la vista previa está incompleta", "When shared, its preview is incomplete"),
      why: t("Sin og:title, og:description y og:image, los enlaces compartidos se ven pobres en redes y mensajería.", "Without og:title, og:description and og:image, shared links look poor on social networks and messaging."),
      action: t("Añade las etiquetas Open Graph con título, descripción e imagen.", "Add Open Graph tags with title, description and image.") };
    case "IMAGES_DESCRIBED": return {
      title: t("Muchas imágenes no tienen texto alternativo", "Many images have no alternative text"),
      why: t("El texto alternativo hace la web accesible y explica las imágenes a las máquinas.", "Alternative text makes the site accessible and explains images to machines."),
      action: t("Describe cada imagen relevante con su atributo alt.", "Describe each relevant image with its alt attribute.") };
    case "NO_NOINDEX_ON_READ_PAGES": return {
      title: t("Hay páginas que piden no aparecer en buscadores", "Some pages ask search engines not to index them"),
      why: t("Una página con noindex no se representa en buscadores mientras siga así.", "A noindex page is not represented in search engines while it stays so."),
      action: t("Quita noindex de las páginas que quieras que se encuentren.", "Remove noindex from pages you want to be found.") };
    case "OFFER_DECLARED": return {
      title: t("Su oferta no está declarada en datos estructurados", "Its offer is not declared as structured data"),
      why: t("Las superficies que leen datos estructurados podrían no relacionarla con lo que ofrece.", "Surfaces that read structured data may not connect it with what it offers."),
      action: t("Declara sus servicios o productos con schema.org Service o Product.", "Declare its services or products with schema.org Service or Product.") };
    default: return { title: id, why: "", action: "" };
  }
}
