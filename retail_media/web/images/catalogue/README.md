# Catálogo visual generado

78 productos ilustrativos: 60 orgánicos (20 por categoría) y 18 patrocinados.
Creación y ajuste mediante la herramienta integrada **image_gen**; sin servicios
externos durante la ejecución de la demo. Exportación WebP con cwebp, calidad 85.
Las cuatro imágenes suman 448,804 bytes. Los originales generados se conservan
en el directorio de imágenes de Codex indicado en cada archivo de procedencia.

| Archivo | Contenido | Prompt final |
| --- | --- | --- |
| [technology.webp](technology.webp) | 20 productos de tecnología | [Prompt](technology.webp.prompt.txt) |
| [home.webp](home.webp) | 20 productos de hogar | [Prompt](home.webp.prompt.txt) |
| [sport.webp](sport.webp) | 20 productos deportivos | [Prompt](sport.webp.prompt.txt) |
| [sponsored-refined.webp](sponsored-refined.webp) | 18 patrocinados, con encuadre separado | [Prompt de ajuste](sponsored-refined.webp.prompt.txt) |

Los JSON contiguos registran procedencia, prompt y referencia de la generación.
[manifest.json](manifest.json) relaciona cada SKU con su región de imagen. El
renderizador conserva proporciones y limita la fotografía a esa región para
que no aparezca un fragmento de otro producto. Cada tarjeta utiliza una imagen
raster generada; el marco SVG solo recorta la región, no dibuja productos.

Las imágenes, nombres y precios son presentación sintética. No constituyen
observaciones de entrenamiento adicionales ni nuevas acciones para el agente.
