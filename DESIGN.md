---
name: Retail Media Lab
description: Sistema visual del laboratorio académico de decisiones de retail media.
colors:
  nav: '#173453'
  nav-hover: '#24466a'
  nav-muted: '#b6cbe2'
  bg: '#f3f6fb'
  surface: '#fff'
  ink: '#1c2d45'
  muted: '#596b82'
  faint: '#edf2f8'
  line: '#dce4ee'
  blue: '#315bd6'
  blue-hover: '#2548b1'
  blue-soft: '#edf2ff'
  blue-text: '#234ba7'
  green: '#176a51'
  green-soft: '#e9f6ef'
  amber: '#8f531b'
  amber-soft: '#fff4e6'
  red: '#a63648'
  red-soft: '#fdf0f2'
  purple: '#6750a5'
  purple-soft: '#f0edf8'
  photo: '#f5f7fa'
  sponsor-line: '#e5c6a4'
typography:
  headline:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 30px
    fontWeight: 650
    lineHeight: 1.18
    letterSpacing: -0.025em
  title:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 22px
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: -0.025em
  title-mobile:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 20px
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: -0.025em
  title-small:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 16px
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: -0.025em
  body:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 12px
    fontWeight: 650
  metric:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 30px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.03em
  evaluation-metric:
    fontFamily: Figtree, Arial, sans-serif
    fontSize: 32px
    fontWeight: 600
    letterSpacing: -0.025em
rounded:
  progress: 3px
  slot: 4px
  tag: 5px
  chip: 6px
  field: 7px
  control: 8px
  product: 10px
  panel: 14px
spacing:
  '4': 4px
  '6': 6px
  '8': 8px
  '10': 10px
  '12': 12px
  '14': 14px
  '16': 16px
  '18': 18px
  '20': 20px
  '22': 22px
  '24': 24px
  '28': 28px
  '32': 32px
  '48': 48px
components:
  button-primary:
    backgroundColor: '{colors.blue}'
    textColor: '{colors.surface}'
    rounded: '{rounded.control}'
    padding: 11px 14px
    height: 44px
  button-primary-hover:
    backgroundColor: '{colors.blue-hover}'
  button-secondary:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.ink}'
    rounded: '{rounded.control}'
    padding: 11px 14px
    height: 44px
  button-secondary-hover:
    backgroundColor: '{colors.faint}'
  button-quiet:
    backgroundColor: transparent
    textColor: '{colors.muted}'
    rounded: '{rounded.control}'
    padding: 11px 14px
    height: 44px
  field:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.ink}'
    rounded: '{rounded.field}'
    padding: 10px 12px
    height: 44px
  navigation:
    backgroundColor: transparent
    textColor: '{colors.nav-muted}'
    rounded: '{rounded.control}'
    padding: 13px 12px
    height: 48px
  navigation-active:
    backgroundColor: '{colors.nav-hover}'
    textColor: '{colors.surface}'
  neutral-chip:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.muted}'
    rounded: '{rounded.chip}'
    padding: 8px 10px
  panel:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.panel}'
  product:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.ink}'
    rounded: '{rounded.product}'
    padding: 12px
  lesson-panel:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.panel}'
    padding: 24px
  reading-section:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.panel}'
    padding: 28px
  candidate-chosen:
    backgroundColor: '{colors.blue-soft}'
    textColor: '{colors.ink}'
    rounded: '{rounded.field}'
    padding: 12px
---

# Design System: Retail Media Lab

## Overview

**Creative North Star: "El laboratorio visible"**

La identidad heredada de azul tinta y blanco se convierte en una interfaz académica de trabajo: la navegación sostiene la orientación, las superficies contienen evidencia y el azul de interacción señala acciones y selección. Figtree mantiene una sola voz para explicaciones, controles y cifras tabulares.

La simulación acompaña cada decisión con una explicación visible y avance manual. Resultados y Modelo amplían el espacio de lectura, alinean títulos, párrafos y evidencia, y reservan las fórmulas y tablas extensas para detalles desplegables. Los bordes suaves separan contenidos; el color semántico acompaña nombres, etiquetas e iconos. La identidad se conserva y la densidad se adapta a la tarea.

**Key Characteristics:**
- Navegación azul tinta y superficies blancas sobre fondo frío.
- Una familia tipográfica local, cifras tabulares y explicaciones con medida de lectura.
- Selección azul, patrocinio ámbar y estados con texto explícito.
- Recorrido manual visible, grid de ancho completo y detalle técnico progresivo.

## Colors

El azul tinta establece el marco; los azules de interacción y los tonos semánticos identifican acciones y evidencia. Los valores normativos están en el frontmatter y corresponden a las variables de `retail_media/web/app.css`.

### Primary
- **Azul de interacción** (`blue`, `blue-hover`): acción principal, foco, progreso y selección actual.
- **Azul de lectura** (`blue-text`, `blue-soft`): etiquetas seleccionadas, candidato elegido y superficies explicativas.
- **Azul tinta** (`nav`, `nav-hover`, `nav-muted`): navegación, estado activo, iconos y texto secundario del marco.

### Secondary
- **Verde de resultado** (`green`, `green-soft`): compras observadas, variaciones positivas, controles superados y finalización.
- **Ámbar de patrocinio** (`amber`, `amber-soft`, `sponsor-line`): posiciones patrocinables, conflictos, advertencias y borde del producto patrocinado.
- **Rojo de alerta** (`red`, `red-soft`): error, resultado negativo y comprobación fallida.
- **Violeta de marca** (`purple`, `purple-soft`): identidad y presupuesto de la segunda marca. Las otras marcas usan azul y verde, siempre junto a su nombre.

### Neutral
- **Fondo frío** (`bg`): lienzo general.
- **Blanco de superficie** (`surface`): paneles, campos y tarjetas.
- **Tinta de contenido** (`ink`) y **texto secundario** (`muted`): lectura principal y explicaciones.
- **Tono tenue** (`faint`) y **línea suave** (`line`): cabeceras de tabla, pistas, divisores y bordes.
- **Fondo fotográfico** (`photo`): respaldo neutro de las fotografías de producto.

**The Evidence Color Rule.** Usa azul para acción y selección; ámbar para patrocinio o conflicto; verde y rojo para el sentido del resultado. Conserva nombres y mensajes junto al color.

## Typography

**Display Font:** Figtree, con Arial y sans-serif como respaldo.  
**Body Font:** La misma familia.  
**Label/Mono Font:** No existe una familia monoespaciada separada; el cuerpo usa `font-variant-numeric: tabular-nums`.

**Character:** Sans de lectura compacta con títulos de peso intermedio y tracking ligeramente cerrado. El archivo variable local `retail_media/web/fonts/Figtree.ttf` cubre pesos 300–900, se sirve con `font-display: swap` y conserva su licencia OFL junto a la fuente.

### Hierarchy
- **Headline:** encabezado de página; token `headline`. Se mantiene en 30px en escritorio y pasa a 26px hasta 680px.
- **Title:** encabezados de las secciones de lectura; token `title`, con token `title-mobile` hasta 680px. El panel guiado usa 21px, 19px en móvil y 18px hasta 360px. El encabezado del catálogo conserva 18px.
- **Title small:** subtítulos y pasos del aprendizaje; token `title-small`. Los subtítulos de fase del recorrido usan 18px.
- **Body:** texto base y explicación principal; token `body`. Los párrafos de lectura y aprendizaje usan interlineado de 1.75; las fases guiadas usan 1.65. La medida compartida es 74ch. Las introducciones de Resultados y Modelo usan 16px y 15px en móvil.
- **Label:** etiquetas de formulario; token `label`. Ayuda y metadatos usan 12–13px; las etapas del recorrido y los disclosures técnicos usan 14px. Los controles mantienen 12px con peso 600. El nombre de producto usa 13px y peso 550; el precio usa 13px y peso 650.
- **Metric:** tres valores observados de Simulación; token `metric`. Se reducen a 23px hasta 680px y a 21px hasta 360px. Las notas usan 11px en móvil.
- **Evaluation metric:** valores destacados de Resultados; token `evaluation-metric`. Se reducen a 28px en móvil, alineados a la derecha de su etiqueta y explicación.

**The Single Voice Rule.** Usa Figtree para títulos, controles y cifras; diferencia la jerarquía mediante tamaño, peso y espacio.

## Layout

El marco de escritorio es un grid con navegación de 192px y contenido flexible. El contenido tiene ancho máximo de 1640px y padding lateral de 32px. Hasta 1250px, la navegación mide 164px y el padding baja a 24px; hasta 1000px pasa a una barra superior; hasta 680px el margen lateral baja a 16px. El espaciado dominante se construye sobre pasos de 4px, con ajustes menores en componentes densos.

La configuración local se presenta sin panel contenedor: escenario y Reiniciar quedan a la vista, mientras Ajustes abre un desplegable de hasta 430px. El recorrido guiado ocupa una superficie propia, con contenido antes de los controles manual y automático; progreso y estado se sitúan debajo. Las tres métricas observadas forman una franja separada por líneas verticales y conservan tres columnas en móvil. El catálogo ocupa el ancho disponible con cuatro columnas fijas y separación de 16px. Hasta 680px usa dos columnas ajustadas al ancho disponible, sin ancho mínimo que fuerce desplazamiento horizontal. La decisión técnica se sitúa debajo del catálogo. Comparación de candidatos, inversión, actividad y mapa usan disclosures cerrados inicialmente.

Resultados y Modelo usan un contenedor de lectura de hasta 1120px; los párrafos comparten medida máxima de 74ch. Las secciones blancas tienen padding de 28px y separación superior de 32px; en móvil cambian a 20px y 24px. Los tres destacados de Resultados comparten filas de etiqueta, valor y nota. Hasta 680px se convierten en filas horizontales: texto a la izquierda, cifra a la derecha. Cada fila del gráfico reserva columnas comunes para etiqueta, barra y valor. Modelo ordena el aprendizaje con números en una columna propia y descripciones alineadas con su título. Las pruebas usan filas de disclosure con estado y apertura a la derecha.

En móvil los controles del recorrido ocupan el ancho, las tablas breves ajustan las palabras y las tablas técnicas mantienen desplazamiento horizontal dentro de su región. Hasta 360px, los controles del recorrido se apilan, el escenario ocupa una fila y la separación del catálogo baja a 8px. Los candidatos usan tres columnas, dos hasta 1100px y una hasta 680px. Las marcas se apilan hasta 680px; el mapa pasa de 20 a 10 columnas.

El catálogo tiene scroll propio: 530px de alto en escritorio, 580px desde 1600px y 500px hasta 680px. Tablas, eventos y candidatos admiten desplazamiento sin expandir el ancho del documento. Las áreas fotográficas conservan proporción cuadrada y ancho `min(100%,144px)`. Los 60 SKUs activos reutilizan fotografías raster de tres atlas WebP locales de 20 productos por categoría; el cuarto atlas, de 18 patrocinados de la versión anterior, se conserva como legado. Hay 16 SKUs anunciables por categoría, también disponibles como orgánicos; las 48 acciones patrocinadas reentrenadas reutilizan estas imágenes, sin fotografías nuevas. El manifiesto `retail_media/web/images/catalogue/manifest.json` define la región de origen de cada imagen; `retail_media/web/catalogue-images.js` valida sus límites y el marco SVG de `retail_media/web/app.js` conserva la proporción con `preserveAspectRatio="xMidYMid meet"` y un `clipPath` limitado a esa región. El SVG enmarca la fotografía; no dibuja el producto.

## Elevation & Depth

Los paneles son planos: fondo blanco, borde suave y sin sombra. La jerarquía depende de tono, separación y estado seleccionado. El desplegable local de Ajustes usa `0 16px 40px rgb(23 52 83 / .12)` para distinguir su posición flotante. La variable heredada `shadow` sigue declarada, pero no determina la sombra de Ajustes. La navegación es sticky en escritorio; los detalles de decisión permanecen en el flujo normal.

**The Quiet Surface Rule.** Los paneles y productos se separan con fondo y borde. La sombra se reserva al desplegable flotante de Ajustes.

## Shapes

Los paneles mayores usan el radio `panel`; productos y mensajes de error usan `product`. Los controles y elementos de navegación usan `control`; campos y filas de candidatos usan `field`. Chips, etiquetas, posiciones y barras emplean radios menores de la escala. Los bordes de contenedor son sólidos de 1px. La selección del producto usa contorno azul de 2px; los productos pendientes conservan el mismo borde sólido. Los indicadores puntuales son círculos o cuadrados pequeños con función de leyenda.

## Components

### Buttons
Controles compactos, con texto explícito y SVG de trazo. La acción primaria usa azul; la secundaria usa blanco con borde; la discreta es transparente. Los tres emplean los tokens de componente del frontmatter, tipografía de 12px y peso 600. La altura documentada de 44px es **mínima**, no una altura fija. Hover cambia el fondo; la secundaria también refuerza el borde y la discreta aumenta el contraste del texto. No se declara un efecto visual `:active` propio. Los botones deshabilitados reducen su opacidad a 0.5 y usan cursor de espera.

### Inputs / Fields
Campos nativos blancos de altura mínima 44px, borde de 1px, padding de 10px 12px y texto de 12px. Labels en texto secundario y peso 650; caret y accent usan azul. El select deja espacio a su indicador nativo. El formulario conserva validación nativa y los estados disabled se controlan durante carga y reproducción; no hay un estilo de error local por campo. Los fallos de servicio usan el banner de alerta con mensaje y Reintentar.

### Navigation
Texto secundario claro sobre azul tinta. El estado activo y hover usan el fondo `nav-hover` y texto blanco; el estado actual también se expone mediante `aria-current`. Los destinos son botones de sección con icono SVG y texto. Se transforma en barra superior hasta 1000px y admite scroll horizontal hasta 680px. En escritorio, la altura mínima es 48px; en la barra es 44px.

### Chips
Los chips neutros son informativos, blancos y con borde; no son botones. Las etiquetas de decisión usan azul suave y texto azul de lectura; las advertencias usan ámbar suave y texto ámbar. El chip de estado de decisión usa tono tenue. Los nombres e iconos sostienen la comprensión cuando el color no es visible.

### Cards / Containers
Los paneles blancos con borde y radio `panel` agrupan grid, recorrido guiado, decisión, campañas, eventos y secciones de lectura. El recorrido usa padding de 24px y 20px en móvil; las secciones de lectura usan 28px y 20px en móvil. La tarjeta de producto usa radio `product`, padding de 12px, borde sólido suave, nombre, precio y fotografía. Hasta 360px, el padding baja a 10px. Los 60 SKUs activos tienen nombres y fotografías propios, con precios variados; nombre e identidad se mantienen coherentes entre tarjeta, candidato, decisión y actividad. Dieciséis por categoría admiten patrocinio y también pueden aparecer como orgánicos. Las imágenes, nombres y precios son metadatos sintéticos de presentación; el modelo PLP16 reentrena las 48 acciones patrocinadas sin usar las imágenes como señales de entrada, como documenta `docs/lab-model-card.md`. Los atlas, prompts y JSON de procedencia se conservan juntos en `retail_media/web/images/catalogue/`. La marca y la etiqueta Patrocinado solo se muestran en productos patrocinados; la condición de orgánico, pendiente o no visto se conserva en el nombre accesible. Hover refuerza el borde, patrocinio usa `sponsor-line` y la decisión actual añade contorno azul. Los productos no vistos mantienen opacidad completa. Un evento observado incorpora texto de clic o compra.

### Detalles progresivos
Los disclosures principales usan un summary de al menos 56px con título, estado breve cuando corresponde e indicador de apertura. Ajustes, mapa y candidatos usan summaries de al menos 44px. Ajustes abre campos locales sobre el formulario; los demás detalles se expanden en el flujo. El detalle técnico de decisión empieza con una indicación breve y permanece cerrado al iniciar o reiniciar; seleccionar un producto con evidencia abre su explicación. Las etapas todavía no reveladas se consultan en el recorrido guiado. Con evidencia, presenta producto, motivo, etiquetas, recompensa y cobro. La comparación de candidatos se abre por separado: la fila elegida tiene fondo azul suave y borde azul; la bloqueada usa tono tenue con motivo textual. El conflicto usa ámbar. Los candidatos conservan scroll y región enfocables.

### Recorrido guiado
La superficie visible presenta Contexto, Opciones y Resultado en ese orden. Las etapas alcanzadas permiten volver a leer; las futuras permanecen deshabilitadas. La etapa actual tiene texto azul, borde inferior azul y `aria-current="step"`. La explicación usa párrafos breves, comparación de opciones cuando procede y un bloque tenue para el resultado observado. La elección y las métricas nuevas se revelan al llegar a Resultado.

La acción primaria situada debajo del contenido cambia de Comenzar recorrido a Ver opciones, Ver decisión y Siguiente decisión. Automático es secundario y opcional; el ritmo de Ajustes permite 8 o 15 segundos por etapa. El resumen de 200 decisiones requiere selección explícita. El estado explica si está pausado o avanzando; cambiar de sección pausa la reproducción. No hay animación decorativa ni cuenta regresiva que presione la lectura.

### Lectura técnica
Resultados comienza por la interpretación y la comparación de conversión; la tabla, los intervalos y las definiciones se abren a demanda. Modelo organiza el aprendizaje en cuatro pasos numerados. Fórmula, curva Brier de validación, semillas y glosario se alojan en disclosures dentro de Modelo. La curva no se presenta como recompensa ni como gráfico de Resultados.

Las comprobaciones de atajos son elementos nativos `details` y `summary`: una fila conserva nombre, estado textual e indicador de apertura; el párrafo explicativo se revela en el flujo. El estado no se comunica solo con verde o rojo.

### Métricas, gráficos y tablas
Los valores iniciales sin evidencia se muestran con raya y explicación. Las cifras tienen ancho tabular. Los gráficos de comparación usan azul para el agente, texto secundario para orgánico y línea suave para otras políticas; cada barra conserva etiqueta y valor. La tabla destaca la política del agente con azul suave. El progreso y la entrega son barras finas, nunca sustitutos de sus cifras.

### Accesibilidad, estados y movimiento
Botones, enlaces, campos, selectores, summary y regiones con tabindex comparten foco azul de 3px con offset de 4px. El enlace para saltar al contenido aparece al enfocarse. Los controles principales respetan 44px de alto. La carga expone `aria-busy`; errores usan `role=alert`; cambios y anuncios usan regiones de estado. La finalización utiliza verde suave y una acción explícita hacia evaluación.

El movimiento es funcional: hover de botones y productos en 0.18s, navegación en 0.2s, progreso en 0.4s ease-out y presupuesto en 0.35s ease-out. El documento usa scroll suave. Con `prefers-reduced-motion: reduce`, el scroll pasa a auto y se eliminan esas transiciones. No existe animación de entrada ni movimiento decorativo continuo.

## Do's and Don'ts

### Do:
- Do conservar los roles semánticos de la paleta y acompañarlos de texto.
- Do mantener controles de al menos 44px de alto y el foco visible de 3px con separación de 4px.
- Do usar áreas fotográficas cuadradas, conservar la proporción de cada producto y mantener los atlas, su manifiesto y su procedencia.
- Do distinguir carga, ausencia de evidencia, candidato bloqueado, error y finalización.
- Do respetar los overrides finales del CSS antes de copiar una regla anterior.
- Do alinear títulos, explicaciones, barras y valores con la retícula de su sección.
- Do conservar el avance manual del recorrido y revelar la evidencia después de explicar las opciones.

### Don't:
- Don't usar solo color para identificar marcas, restricciones o resultados.
- Don't convertir una métrica aún no observada en un resultado visual positivo.
- Don't agregar sombras a los paneles de contenido ni estirar las imágenes del catálogo.
- Don't añadir tipografías externas o una familia distinta para los números.
- Don't convertir el encabezado compacto de la herramienta en una portada de marketing.
- Don't añadir eyebrows: el usuario confirmó encabezados directos sin esas etiquetas.
- Don't adelantar el resultado de una decisión en Contexto u Opciones.
