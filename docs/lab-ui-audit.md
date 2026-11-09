# Auditoría Impeccable — Retail Media Lab

Fecha de trabajo: 30 de octubre de 2026. Superficie: `retail_media/web/`, modo
Operate, audiencia académica. El encargo incluyó construir y corregir la demo;
esta auditoría registra el diagnóstico y la evidencia final. No se hicieron
commits ni push durante la implementación.

## Integridad de implementación

**Pass dentro del alcance inspeccionado.** El grid de veinte posiciones y ocho
spots patrocinables usa inferencia del motor Python, no decisiones inventadas
en JavaScript. El inspector distingue estimación, evento observado, recompensa
y cobro. Las secciones Resultados y Modelo muestran comparadores fuertes,
fallas de entrega y limitaciones. El código, el modelo y la evaluación tienen
identidades vinculadas; un reporte de otro modelo se marca obsoleto.

Se inspeccionaron ocho capturas válidas en
`.impeccable/review/final/screenshots/`: escritorio a 1440 y 1920px, tablet a
768px, móvil a 390 y 320px, Resultados en escritorio/móvil y Modelo. La única
corrección material solicitada por el finish reviewer fue retirar una etiqueta
decorativa encima del objetivo. El reviewer puntuó el arreglo como **resolved**
y devolvió **ship al alcance del arreglo revisado**, sin regresión visible.

## Salud técnica

| Dimensión | Nota / 4 | Evidencia y límite |
|---|---:|---|
| Accesibilidad | 3 | Axe-core 4.10.3: cero violaciones automáticas WCAG 2A, 2AA y 2.1AA en las tres vistas; teclado y foco visibles comprobados. No se probó un lector de pantalla real. |
| Rendimiento | 4 | Aplicación sin framework ni build; fuente local de 62 KB y sprite WebP de unos 85 KB. Veinte tarjetas, cola de eventos acotada y modelo congelado compartido entre simulaciones. |
| Theming | 3 | Colores semánticos y tipografía local coherentes. Superficie deliberadamente clara; no se ofrece modo oscuro ni conmutación de temas. |
| Responsive | 3 | Sin overflow de página en 320/390/768/1440/1920px; controles visibles ≥44px en móvil. Viewports con emulación táctil; no se validaron gestos en un teléfono físico. |
| Integridad de implementación | 4 | Simulación causal, controles funcionales, estado exportable y errores explícitos; hechos sintéticos identificados y reportes ligados al modelo. |
| **Total** | **17/20** | **Good**. No quedan arreglos materiales conocidos de la revisión; las notas conservadoras reflejan límites de cobertura y alcance. |

Las notas no constituyen certificación WCAG ni sustituyen pruebas de rendimiento
de producción, un estudio con usuarios o una auditoría completa del modelo.

## Hallazgos y resolución

### P2 — Texto de metadatos demasiado pequeño

- Ubicación: `web/app.css`, tarjetas, inspector, leyendas y etiquetas.
- Impacto: dificultaba leer la demostración a distancia y en pantalla móvil.
- Corrección: mínimo de 12px en metadatos, nombres de producto de 13px,
  párrafos de interfaz entre 12–14px y encabezados diferenciados. El gráfico
  de validación recalcula su viewBox con el ancho real para no miniaturizar sus
  etiquetas al reducir pantalla.
- Comando de referencia: `$impeccable typeset`. **Resuelto**.

### P2 — Regiones con aria-label sin rol que admita nombre

- Ubicación: `web/index.html`, métricas, mapa de spots y áreas de scroll.
- Impacto: los nombres de algunas regiones no estaban bien soportados en el
  árbol de accesibilidad. Axe los pedía revisar manualmente.
- Corrección: roles group/region apropiados, labels y tabindex en las áreas de
  scroll. Repetición de axe: ninguna revisión pendiente de ese tipo.
- Comando de referencia: `$impeccable harden`. **Resuelto**.

### P2 — Evidencia obsoleta tras cambiar el modelo

- Ubicación: `lab_server.py`, `/api/evaluation`, y estado de Resultados.
- Impacto: reentrenar podía dejar visibles cifras de otro artefacto.
- Corrección: model_id de parámetros y estructura; API responde stale cuando
  difiere; el cliente limpia métricas, curva y checks anteriores. Test HTTP y
  prueba de estado en navegador verifican la transición.
- Comando de referencia: `$impeccable harden`. **Resuelto**.

### P3 — Persistencia de scroll entre secciones

- Ubicación: `web/app.js`, navegación de vistas.
- Impacto: cambiar de sección podía abrirla por debajo de su encabezado.
- Corrección: cambio de sección explícito vuelve al inicio, conservando el foco
  de navegación y la jerarquía de lectura. **Resuelto**.

### P3 — Etiqueta decorativa sobre el objetivo

- Ubicación: `web/index.html`, objective-box de Modelo.
- Impacto: incumplía el craft floor de Impeccable para eyebrows.
- Corrección: retirada la etiqueta; se conserva «Una sesión. Una primera compra».
  Modelo recapturado y arreglo verificado por reviewer independiente.
- Comando de referencia: `$impeccable polish`. **Resuelto**.

## Detector y comprobaciones manuales

El detector mecánico de Impeccable señaló dos casos de cramped-padding en los
divisores de métricas. La comprobación renderizada mostró border-left de 0px
cuando el padding izquierdo era 0; los divisores reales tenían padding de 24px.
Eran falsos positivos de la combinación de shorthand y selector responsive.
Se hicieron explícitos los resets `border-left:0`. El detector mantuvo esos
falsos positivos, por lo que se registró una excepción de cramped-padding
limitada a `retail_media/web/index.html`, con las medidas renderizadas como
justificación. No se cambió la composición para esconder un problema real.
La excepción previa de la plantilla histórica `retail_media/report.html` se
conserva por separado. También se exceptúa únicamente Avenir en esa plantilla:
es el reporte anterior, no una fuente nueva del sistema Figtree del laboratorio.
No se deshabilitan archivos completos ni reglas para todo el proyecto.

Axe no pudo determinar automáticamente el fondo de cuatro etiquetas SVG del
gráfico de validación. Se verificó su color `#596b82` sobre blanco: contraste
**5.45:1**. Los demás pares semánticos de texto comprobados también superan
4.5:1: cuerpo 13.90, texto secundario sobre el fondo 5.04, navegación 7.64,
botón primario 5.84, patrocinio 5.65, éxito 5.87 y error 5.84.

## Interacciones ejercitadas

- Nueva simulación y ajustes aplicados al reiniciar; configuración activa
  conservada al exportar, aunque el formulario tenga cambios pendientes.
- Una decisión, ocho oportunidades, reproducción rápida, pausa y finalización.
- Inspector con 19 candidatos, eventos de clic/compra, recompensa y CPC reales.
- Exportación JSON con configuración, model_id y snapshot observado.
- Navegación Simulación/Resultados/Modelo y cambio de escenario de evaluación.
- Aviso de evaluación obsoleta con tablas y comprobaciones antiguas retiradas.
- Trayectoria escasa de 55 visitas efectivas sobre 250 previstas: saldo pendiente
  visible y controles de avance deshabilitados al terminar.
- Navegación con Tab, foco de 3px y controles con labels. Regiones de scroll
  accesibles por teclado; prefers-reduced-motion retira transiciones manteniendo
  los cambios de estado.

Los gestos nativos de scroll y select se revisaron por estructura y emulación
de viewport, no en hardware táctil físico. No se simula una certificación
automática a partir de una captura de pantalla.

## Patrón del sistema y acciones siguientes

Mantener separación visual y semántica entre conversión, entrega y evidencia.
Conservar tokens, iconos coherentes, contenido local, slots numerados y controles
nativos. No convertir un reward alto en una afirmación de éxito del negocio.

Para una futura entrega con validación adicional: probar lector de pantalla y
hardware táctil real (`$impeccable audit` / `$impeccable adapt`), medir arranque
en equipos más lentos (`$impeccable optimize`) y cerrar cualquier cambio con
`$impeccable polish`.

## Revisión de simplificación solicitada por el usuario

La simulación anterior fue rechazada por exceso de texto y densidad. Esta
revisión elimina los párrafos introductorios, los lemas, la nota lateral y las
etiquetas orgánicas repetidas. El catálogo ocupa el ancho disponible y muestra
tres métricas: conversión, cambio frente a orgánico y gasto CPC. Ajustes,
explicación de la decisión, candidatos, mapa de posiciones, inversión por marca
y actividad se abren bajo demanda. Las funciones del motor y su evaluación no
se modifican. Las capturas anteriores documentan el estado previo; la evidencia
vigente de esta revisión está en `.impeccable/review/clean/`.

Verificación de esta revisión:

- Vistas de 320, 390, 768 y 1440px, con detalles cerrados y abiertos. Se corrigió
  el mínimo implícito del grid que causaba desbordamiento en 320px.
- Paso individual, inspección explícita de producto con 19 candidatos, pausa,
  cambios de política/escenario y finalización real de un escenario escaso.
- Ajustes cerrados revelan los campos inválidos; Enter abre y Escape cierra el
  panel, devolviendo el foco al summary con contorno de 3px.
- Resultados conserva sus siete políticas; Modelo conserva sus nueve controles.
  La actividad resume clics y compras; exportar mantiene el snapshot completo.
- Consola sin errores ni avisos. `node --check retail_media/web/app.js`,
  `git diff --check` y 65 pruebas de Python correctas. No se repitió axe en esta
  revisión; sus resultados anteriores no se atribuyen a este cambio.
- Sin nuevas supresiones del detector, sin commits ni push. Preview temporal,
  sesión de simulación y pestaña de pruebas cerrados al terminar la validación.


## Recorrido guiado y lectura técnica — 2026-11-01

A petición del usuario, la demo vuelve a explicar cada decisión sin recuperar
la densidad anterior. Avance manual inicial por Contexto, Opciones y Resultado.
El snapshot pendiente se mantiene separado del visible: elección y métricas no
se revelan hasta Resultado. Automático optativo: 8 o 15 segundos por etapa;
resumen explícito agrupa 200 decisiones. No se modifica el objetivo, la política
ni el modelo entrenado; el motor solo añade contexto anterior a la decisión y
aclara el texto de bloqueo por ritmo.

Resultados usa lectura de «compras por cada 100 visitas» antes de los detalles
estadísticos. Modelo ordena experiencia, estimación, planificación y restricciones;
conserva fórmulas, pruebas, validación y glosario mediante disclosures. Títulos
directos sin eyebrows, cuerpo de lectura de 14px y alineación común.

Evidencia vigente: `.impeccable/review/guided/`, doce capturas de 320, 390,
768 y 1440px. La tabla de la explicación ya envuelve su caption y cabe en 320px.
Se verificaron las siete políticas, métricas sin revelación anticipada, pausa con
cero temporizadores, cambios de pestaña, etapas con Enter/foco de 3px, ajustes con
Escape, finalización en modo resumen y retirada de evidencia ante estado obsoleto
o error de conexión. No se probaron lector de pantalla ni dispositivos físicos.

66 pruebas Python y pruebas Node de explicaciones/ritmo correctas. Detector
acotado de layout: `[]`; consola sin errores en la verificación. Sin nuevas
supresiones, commits ni push. El preview y la pestaña de pruebas se cierran al
terminar. La revisión independiente y el sistema de diseño se guardan junto a
la evidencia vigente.

Veredicto independiente: `ship` para la interfaz revisada. La comprobación
posterior de teclado detectó pérdida de foco al deshabilitar el botón durante
una petición; se corrigió restaurándolo solo cuando seguía en el body. Tres
pulsaciones consecutivas de Enter recorrieron las fases 0, 1 y 2 conservando
el botón y su foco de 3px. El revisor calificó esta corrección y la sincronización
documental como resueltas. Preview PID3918, sesión y pestaña temporal cerrados;
no quedaron procesos propios de la tarea activos.


Ajuste de columnas solicitado: cuatro productos por fila en escritorio y tablet,
dos en móvil (hasta 680px). Retirado el ancho mínimo móvil de 640px. Comprobado
en navegador a 320, 390, 680, 681, 768, 1440 y 1920px: columnas 2/2/2/4/4/4/4
sin desplazamiento horizontal del catálogo. Pestaña temporal cerrada; el servidor
se mantiene activo a petición del usuario para probar la demo.


## Catálogo distinguible — 2026-11-01

60 productos orgánicos (20 por categoría) y 18 patrocinados con nombres, precios
e imágenes distintos. Fotografías generadas con image_gen, servidas mediante
cuatro WebP locales de 448,804 bytes. Prompts, referencias y manifiesto están
en `retail_media/web/images/catalogue/`. Escaneo: cuatro rasters, cero sin
procedencia. Se corrigieron encuadres de imágenes agrupadas; las regiones SVG
solo muestran los píxeles de cada producto y mantienen sus proporciones.

La presentación se aplica a tarjetas, candidatos y eventos de forma coherente.
Pruebas comparan la simulación decorada con la original para demostrar igualdad
de acciones, contabilidad, reward y CVR; los perfiles y el artefacto entrenado
se conservan. No representa entrenamiento sobre nuevas imágenes ni 78 acciones.

72 pruebas Python, pruebas Node de 78 regiones locales únicas y pruebas de
explicaciones correctas. Navegador a 320/390/768/1440px: 20 nombres distintos,
20 fotos cargadas y columnas 2/2/4/4, sin desbordamiento. Consola sin errores.
Revisión independiente: ship dentro del alcance del catálogo; sistema de diseño
y sidecar sincronizados. Las capturas `*-gallery.png` en review/catalogue son
fixtures de revisión con scroll expandido para examinar todos los productos,
no una ejecución que coloque 18 anuncios simultáneos.

Sin nuevas supresiones, commits ni push. Generación y exportadores finalizados;
sesión y pestaña de pruebas liberadas. Se deja únicamente el preview solicitado
por el usuario, PID11122 en puerto8765, para que pueda revisar el resultado.

## Impresiones por clusters — 2026-11-01

Refinamiento con Impeccable clarify y revisión técnica audit. Se aclaró Q como
probabilidad estimada de primera compra restante, con porcentaje y muestra 3/4.
Por corrección del usuario, la propuesta de comparar dos productos se reemplazó
por clusters definidos antes de la réplica por aporte esperado a conversión.
No se usan puja ni exposición final para definir winners. No cambió el selector,
el modelo ni la recompensa. Se ofrecen total y promedio por todos los miembros;
se muestran 18 candidatos y causas de exclusión al abrir detalles.

Capturas vigentes de Resultados: `.impeccable/review/plp-clusters/` a 1440,
738 y 390px, además de promedio, balance y barras expandidas. Opciones conserva
las capturas `.impeccable/review/plp/options-*.png`. Las anteriores curvas de
parejas en `review/plp/` son historia de una propuesta reemplazada por solicitud
del usuario. No son evidencia del gráfico vigente.

Auditoría acotada a lo cambiado (no certificación WCAG ni revisión de otros
navegadores): integridad coherente, paleta y Figtree conservadas, sin eyebrows,
selectores etiquetados de 44px, foco de 3px y curva con nombre accesible; sin
animación añadida. Puntaje orientativo: accesibilidad 3/4, rendimiento 4/4,
theming 3/4 (tema claro previsto), responsive 3/4 (Chromium emulado, sin teléfono
físico), integridad 4/4: 17/20. La tabla técnica desplaza dentro de su región;
la página no desborda en los tres tamaños. No se probó lector de pantalla real.

Detector `plp-audit.json`: cero hallazgos primarios y un advisory preexistente
sobre radio de 2px del pequeño marcador de leyenda `<i>`, fuera de la escala
publicada. Se deja standing, sin alterar esa parte ni suprimir reglas. No se
introdujeron ignores. La primera revisión señaló marcas visibles en barras de
valor cero; se corrigió `min-width:0` en el gráfico nuevo y se verificó ancho
real 0 en las 15 filas sin impresiones.

78 pruebas Python y tres suites Node pasan. Las nuevas pruebas reconcilian
impresiones, elegibilidad, exclusiones, CPC y marcas, comparan snapshots con/sin
observador y comprueban grupos fijos, reproducción y denominadores con ceros.
Navegador: 24 combinaciones escenario×PLP×escala, 18 filas y dos curvas en cada
una; fallos de red ocultan cifras previas y permiten reintentar; reporte de otro
modelo se oculta; consola sin errores. Se comprobó foco visible del selector;
la automatización no confirmó cambiar opción desde el popup nativo. Esto no
establece un fallo del control.

Cierre documental de la extensión: revisión independiente `clusters_finish_review`
con disposición `ship`, nueve capturas vigentes válidas (seis de clusters y tres
de Opciones) y sin correcciones materiales pendientes. Esta pasada documental
contrastó `index.html`, `app.css`, `app.js` y `clusters.js` con `PRODUCT.md`,
`DESIGN.md`, el sidecar y `docs/lab-impression-allocation.md`; no repitió pruebas
de navegador. Los 23 colores normativos coinciden con las variables CSS; curvas
y barras reutilizan azul, tinta y texto secundario, Figtree local y cifras
tabulares. Campos nativos, disclosures, foco de 3px con separación de 4px y
breakpoint móvil de 680px permanecen dentro del sistema existente.

El contrato de la extensión se registra en el surface brief. `DESIGN.md` y
`.impeccable/design.json` se conservan sin cambios: no se incorpora una nueva
escala ni se convierte el radio advisory de 2px en regla del sistema. Sin
supresiones nuevas. Esta pasada solo editó documentación y no inició procesos
persistentes, servidores ni sesiones de navegador.

Recursos al finalizar: preview propiedad de esta tarea, PID 21121, sesión 91663,
`python3 -m retail_media lab --port 8765`, se mantiene por petición previa del
usuario para revisar la demo. HTTP 200 e informe v2 compatible. Previews
anteriores 11122 y 17671 terminaron y se verificaron ausentes. La simulación y
pestaña de pruebas 7 se eliminaron; no se cerró el navegador del usuario ni la
página vacía administrada por la aplicación. Sin descendientes del preview,
0% CPU y unos 35 MB RSS en la comprobación final. Generador, tests y helpers
concluidos; no quedan otros procesos temporales de esta pasada.

## Cierre de la extensión PLP16 — 2026-11-01

La corrección solicitada por el usuario queda reflejada en la superficie:
16 anuncios propios de cada PLP, primera exposición de cada anuncio apto antes
de concentrar el reparto y dos cohortes fijas de 8. Winners y Losers expresan
prioridad relativa por valor aprendido; no se construyen con pujas ni con las
impresiones finales. Las curvas conservan total y promedio por todos los miembros,
cobertura real y mínimo por anuncio. El detalle separa pérdidas por ranking,
recuperación de pacing y cobertura inicial, sin mezclarlas con exclusiones.
La explicación guiada identifica la primera exposición cuando causa la elección.

Modelo muestra 88/100 frente a 55/100 mediante una rúbrica técnica propia de esta
entrega académica. No es accuracy, probabilidad de éxito ni certificación. Sus
razones y límites quedan en un disclosure; el reporte compatible debe estar
disponible para mostrar la cifra. El entrenamiento comprende 48 acciones
patrocinadas más orgánico y 900,000 transiciones; la evaluación separada comprende
224 ejecuciones sobre ocho semillas. Se observó cobertura 48/48 en los 32/32 días
del agente y ningún sobregiro en las 224 ejecuciones. Es evidencia del simulador,
no garantía de cobertura o conversión bajo cualquier tráfico real. La ficha
`docs/lab-model-card.md` y `docs/lab-impression-allocation.md` detallan el alcance.

El finish review independiente `plp16_finish_review` devuelve **ship**, sin
correcciones materiales pendientes. La revisión de backend `plp16_code_review`
no dejó hallazgos Critical/Important; su observación menor sobre `lost_coverage`
se corrigió y verificó con nueve pruebas dirigidas de competencia. La evidencia
visual vigente son siete capturas en `.impeccable/review/plp16/`:
`desktop.png`, `mobile.png`, `user-738.png`, `model-desktop.png`,
`model-mobile.png`, `simulation-desktop.png` y `simulation-mobile.png`.
La rúbrica está abierta en escritorio y cerrada en móvil; esas imágenes no
demuestran por sí solas una interacción con el disclosure móvil.

Esta pasada documental contrastó `index.html`, `app.css`, `app.js`, `lesson.js`
y `clusters.js` con `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json` y el
surface brief. Inspeccionó las siete capturas existentes, sin abrir navegador ni
repetir sus interacciones. Los 23 colores normativos coinciden con las variables
CSS. Se conservan Figtree local, cifras tabulares, foco azul de 3px con separación
de 4px, campos de 44px como mínimo, superficies planas, disclosures y curva azul
continua frente a tinta discontinua. El grid mantiene cuatro columnas de
escritorio y dos hasta 680px; el recorrido sigue manual y sin eyebrows. No se
añadieron imágenes ni una dirección visual. La referencia heredada
`seed:62070e9cbaea0d93` concuerda con `.impeccable/review/seed-evidence.txt`.

La verificación de interfaz de la implementación registró 24 combinaciones
escenario × PLP × escala, con 16 filas, dos curvas y grupos de 8/8; mínimo
observado al menos 1. Registró 20 SKUs únicos por grid y ausencia de overflow de
página; los estados de error o informe obsoleto retiraron curvas y calificación.
Esos resultados proceden de la validación de la implementación; esta pasada
documental no afirma haberlos ejercitado de nuevo. La validación final de la
tarea principal confirmó 86 pruebas Python y tres suites Node correctas; las API
de evaluación y competencia respondieron HTTP 200, estado ready y controlador
`plp16-min1-v1` compatible. No se probó lector de pantalla, dispositivo físico
ni comprensión de estudiantes.

El detector acotado `.impeccable/review/plp16-audit.json` conserva cero hallazgos
primarios y el advisory preexistente del radio de 2px del marcador `<i>` de la
leyenda. No se canoniza ese radio ni se introducen supresiones. `DESIGN.md` corrige
únicamente dos descripciones factuales del catálogo: 60 SKUs activos, 16
anunciables por categoría y 48 acciones patrocinadas reentrenadas que reutilizan
las fotografías existentes; el atlas anterior de 18 patrocinados se conserva
como legado. Los mismos SKUs también pueden aparecer como orgánicos. No se
cambian tokens, escalas ni paleta; el sidecar se preserva. El contrato actualizado
de esta extensión está en el surface brief.

Esta pasada anexó el cierre a `docs/lab-ui-audit.md` y corrigió esas dos frases
de `DESIGN.md`; no cambió código, reportes, tokens ni el sidecar, no hizo commits
o push y no inició procesos persistentes. El preview de la tarea, PID 26685, sesión 84197, puerto 8765, queda
bajo responsabilidad de la tarea principal por petición previa del usuario. La
tarea principal confirmó la eliminación de la simulación de QA y el cierre de la
página temporal 8; la página vacía administrada por la aplicación se conservó.
El preview observado tenía 0% de CPU, unos 46 MB RSS y ningún descendiente.
