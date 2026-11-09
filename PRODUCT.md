# Retail Media Lab

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

El usuario confirmó que esta versión se dirige a una entrega académica:
ver al agente decidir y explicar su aprendizaje es la prioridad. Debe permitir
demostrar el modelo en una simulación web funcional. No hay clientes ni usuarios
reales conectados.

## Product Purpose

Mostrar cómo un agente elige productos patrocinados en un grid con scroll,
protegiendo la conversión de la web y respetando inversión de las marcas.

## Operating Context

Bloques de 20 productos en cuatro columnas en escritorio y tablet, y dos en móvil; spots patrocinables 3, 4, 5, 6, 11, 12, 13 y 14.
Cobro CPC confirmado por el usuario. Campañas con presupuesto y saldo continuo.
Se requiere demo, simulación y explicaciones de las decisiones, junto con
evaluación y controles dirigidos a detectar reward hacking.

## Capabilities and Constraints

Datos sintéticos, ejecución local, modelo entrenado y comparación de políticas.
Catálogo de 20 SKUs por categoría,16 de ellos anunciables por PLP (48 acciones patrocinadas en total).
El modelo PLP16 se reentrena con 900,000 transiciones factuales. Los anunciantes
aptos reciben al menos una exposición antes de concentrar por conversión; si
falta tráfico, saldo o soporte se informa cobertura pendiente. Las imágenes no
son señales de entrada y los SKUs no se repiten dentro de un bloque.
No modificar servicios externos. En esta entrega no hacer commits ni push.
No afirmar garantías de CVR real ni ausencia universal de reward hacking.
Preservar código y resultados previos para comparar con la versión nueva.

## Brand Commitments

Idioma español. Se conserva la identidad reconocible azul tinta y blanco del
laboratorio existente; el usuario solicita una interfaz muy cuidada y funcional.
Sin eyebrows. La demo prioriza explicaciones breves por etapa y avance manual;
la reproducción automática es opcional y debe permitir leer cada paso.
El nombre de trabajo Retail Media Lab es una decisión de implementación.

## Evidence on Hand

Código NumPy, modelos y evaluaciones sintéticas en artifacts/ y reports/.
No existen datos de producción, resultados de experimentos con personas,
testimonios ni certificaciones de seguridad del modelo.

## Product Principles

- La demo debe ejecutar inferencia y simulación nuevas, con resultados causales.
- Conversión y entrega se evalúan por separado y con denominadores visibles.
- No presentar gasto como éxito de conversión ni esconder restricciones inviables.
- Cada resultado debe poder reproducirse con su configuración y semilla.
- La política debe explicar por qué un candidato se elige, se bloquea o se descarta.
