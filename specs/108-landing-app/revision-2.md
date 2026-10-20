# Revisión 2 · comentarios visuales del CTO

Modo **EXPLORE**, misma PR #350 y base revisada `637ba6542debf1b6ba610b4d85bb35410bed98ab`. Código de esta revisión: `d236a3e3b0b7411c95dba1fe243b77e8c214cf87`.

La revisión responde a la observación humana de una página demasiado plana y de movimiento imperceptible. El recorrido conserva preguntas, fechas, evidencia y contrato comercial. El cambio persigue que el visitante vea la conexión, reconozca dónde está y compare las dos ofertas con claridad.

## Cambios verificables

- Acceder tiene borde, fondo transparente y el mismo tamaño de acción del header. En móvil está también en el menú.
- Los capítulos de navegación tienen número y estado de ubicación; el desplazamiento sigue siendo nativo. Volver arriba devuelve el foco al H1 y tiene enlace en el footer y acceso flotante.
- La asesoría humana se presenta completa, junto a la oferta de software, con su importe visible y sus condiciones. La organización adicional tiene mayor peso tipográfico. Los cálculos siguen importando el contrato comercial.
- El Observador original explica la confianza desde su ilustración, con una nota sobre las fuentes, en lugar de un icono.
- El footer combina identidad, invitación al boletín, grupos de enlaces con jerarquía y controles accesibles. El canal se carga al abrir la solicitud: reutiliza AO-15/AO-16 y sus avisos y consentimientos. En este standalone devuelve disponibilidad desconocida; no se afirma suscripción ni entrega.

## Narrativa y GSAP

Antes, el motor sólo se solicitaba tras el primer gesto, cuando la escena inicial podía haber quedado atrás. Ahora se prepara mediante un chunk diferido cuando la escena entra en pantalla, después de load, fuentes, dos frames e idle. La secuencia ordena capacidad declarada → contexto público → conexión → oportunidad potencial. Dura aproximadamente 2,5 s y tiene un control explícito «Ver cómo conecta».

Las ilustraciones intactas de método y confianza acompañan sus bloques al entrar. Cambiar una fecha o abrir la evidencia tiene una transición acotada. No hay pinning, scrub, bucle automático ni captura del scroll; el texto y los CTA permanecen visibles y utilizables. El movimiento no crea señales ni modifica verdad económica.

La preferencia reducida evita el motor, desactiva repetir y revierte timelines y triggers. Se comprobó por teclado `aria-pressed=true`, repetir desactivado y cero transformaciones/opacidades inline restantes. «Volver arriba» enfoca `lab-heading`. La matriz final verifica 18 casos en seis idiomas, entre 320 y 1920 px, sin desbordamiento; el cálculo también comprueba los límites de ambos paneles de precio. La escena y su control mantienen separación en los seis idiomas a 320 px. La verificación final también corrigió 14 textos con codificación dañada y comprobó su lectura en navegador.

## Evidencia y validación

Las capturas actuales y los informes se guardan en [revision-2](evidence/revision-2/). Las 23 capturas anteriores conservan su procedencia y documentan la primera propuesta; no se han sobrescrito ni declarado Golden Master.

Python: 2.711 PASS, siete omisiones conocidas, 404,38 s. Frontend: 380 PASS, cero omisiones. Ruff, mypy, TypeScript, build, HTML/SEO, Architecture Guard y Graphify comprobados. Los resultados de gobernanza y Lighthouse se adjuntan con su alcance real. El boletín se verifica en estado no disponible, sin enviar datos personales ni fabricar una confirmación.

Autoridad: MASTER, Constitución, ADRs y contratos de la especificación 107; identidad oficial y Design System. Invariantes: POTENTIAL/OBSERVED/UNKNOWN, procedencia y límites temporales sin cambios. La revisión no afecta la homepage aceptada ni el runtime económico.

Estado: **IMPLEMENTADO + PROBADO EN NAVEGADOR + HUMAN_VISUAL_ACCEPTANCE_PENDING**. Sin merge ni despliegue. La frase del CTO «en general la veo bien» es feedback parcial, no aceptación de esta revisión.
